# devops-journey-v2

> **Pipeline de despliegue completo** — una API containerizada que viaja sola, probada y empaquetada, desde el código hasta correr en Kubernetes a escala. Proyecto final de la **Fase 1** de mi ruta DevOps enfocada a IA (MLOps / LLMOps).

Este repositorio demuestra el **ciclo DevOps de punta a punta**: un cambio de una línea en el código se prueba, se construye, se publica como imagen Docker y se despliega en un clúster de Kubernetes con réplicas y sin downtime — sin tocar un servidor a mano. La infraestructura de nube se define como código con Terraform.

---

## El ciclo que implementa este proyecto

```
 [1] MI MÁQUINA                    [2] GIT + GITHUB
 ┌──────────────┐   git push       ┌──────────────────┐
 │  Escribo     │ ───────────────► │   Repositorio    │
 │  código      │                  │   versionado     │
 │  (app.py)    │                  │   (ramas, PRs)   │
 └──────────────┘                  └────────┬─────────┘
                                            │ dispara
                                            ▼
 [4] REGISTRO (GHCR)              [3] CI/CD (GitHub Actions)
 ┌──────────────────┐  push img   ┌──────────────────────┐
 │  Imagen Docker   │ ◄────────── │  1. Corre pruebas    │
 │  publicada       │             │  2. Si pasan: build  │
 │  :main           │             │  3. Publica imagen   │
 └────────┬─────────┘             └──────────────────────┘
          │ pull
          ▼
 [5] KUBERNETES                   [6] USUARIOS
 ┌──────────────────┐             ┌──────────────┐
 │  3 réplicas      │ expone vía  │  Acceden a   │
 │  balanceadas     │ ──────────► │  la app sin  │
 │  sin downtime    │  Service    │  downtime    │
 └──────────────────┘             └──────────────┘
          ▲
          │ corre sobre
 ┌──────────────────┐
 │  [7] TERRAFORM   │  Define la infraestructura (red, VMs)
 │  infra como código│  de forma reproducible en AWS.
 └──────────────────┘
```

---

## Stack

| Capa | Tecnología |
|---|---|
| API | Python 3.12 · FastAPI · Uvicorn |
| Pruebas | pytest |
| Contenedores | Docker · Docker Compose |
| CI/CD | GitHub Actions → GitHub Container Registry (GHCR) |
| Orquestación | Kubernetes (minikube) · Deployment · Service · ConfigMap · Ingress |
| Infraestructura como Código | Terraform · AWS (VPC, Subnet, Security Group, EC2) |

---

## Estructura del repositorio

```
devops-journey/
├── .github/
│   └── workflows/
│       └── docker.yml        # CI/CD: pruebas → build → push a GHCR
├── mi-api/
│   ├── app.py                # API FastAPI
│   ├── requirements.txt      # Dependencias
│   ├── test_app.py           # Pruebas automatizadas (la "compuerta")
│   ├── Dockerfile            # Receta de la imagen
│   ├── .dockerignore
│   └── docker-compose.yml    # Stack local: API + PostgreSQL
├── deployment.yaml           # K8s: 3 réplicas, con probes de salud
├── service.yaml              # K8s: expone y balancea el tráfico
├── configmap.yaml            # K8s: variables de entorno
├── ingress.yaml              # K8s: enrutamiento HTTP
├── terraform-aws/
│   └── main.tf               # Infraestructura AWS (VPC, subnet, SG, EC2)
├── .gitignore
└── README.md
```

---

## Cómo ejecutarlo

### 1. Correr la API en local

```bash
cd mi-api
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash) · en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Endpoints:
- `http://127.0.0.1:8000/` → mensaje raíz
- `http://127.0.0.1:8000/salud` → healthcheck
- `http://127.0.0.1:8000/docs` → documentación interactiva (Swagger)

Pruebas:

```bash
pytest
```

### 2. Con Docker

```bash
cd mi-api
docker build -t mi-api:v1 .
docker run -d -p 8000:8000 --name api mi-api:v1
```

O el stack multi-servicio (API + PostgreSQL):

```bash
docker compose up -d
docker compose down    # -v para borrar también el volumen de datos
```

### 3. En Kubernetes (minikube)

```bash
minikube start --driver=docker
minikube addons enable ingress

kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

kubectl get pods            # esperar a 3 pods en Running (READY 1/1)
minikube service mi-api-service   # abre la app en el navegador
```

Probar los superpoderes:

```bash
kubectl scale deployment mi-api --replicas=5      # escalar
kubectl rollout restart deployment/mi-api         # actualizar sin downtime
kubectl rollout status deployment/mi-api
```

### 4. Infraestructura con Terraform

> Requiere una cuenta de AWS y el AWS CLI configurado (`aws configure`).

```bash
cd terraform-aws
terraform init
terraform plan       # previsualiza — no crea nada
terraform apply      # crea VPC + subnet + security group + EC2
# ... verificar ...
terraform destroy    # ⚠️ SIEMPRE destruir al terminar (control de costos)
```

---

## Decisiones de diseño

- **Cache de capas en el Dockerfile.** Se copia `requirements.txt` e instalan dependencias *antes* de copiar el código, para que Docker reutilice la capa de dependencias mientras solo cambie el código.
- **La "compuerta" en CI/CD.** El job de build usa `needs: test`: la imagen **nunca** se publica si las pruebas fallan. Nunca se publica código roto.
- **Credenciales fuera del código.** Se usan `secrets` de GitHub Actions y el `~/.aws/` para Terraform. Ninguna clave vive en el repositorio.
- **`readinessProbe` + `livenessProbe`.** La readiness garantiza cero downtime durante un rolling update (no llega tráfico a un pod hasta que `/salud` responde); la liveness reinicia pods que dejan de responder.
- **ConfigMap conectado al Deployment** vía `envFrom` — la configuración se inyecta desde fuera, no se hornea en la imagen.
- **AMI dinámico en Terraform.** Se usa un `data source` para tomar el Amazon Linux más reciente en vez de un ID fijo, evitando el error de "AMI no encontrado" y haciendo el código portable entre regiones.

---

## Lo que aprendí

- La diferencia real entre **imagen** y **contenedor**, y por qué el orden de las capas del Dockerfile importa.
- Cómo una **compuerta de CI/CD** protege producción, y por qué las credenciales siempre van en `secrets`.
- El modelo **declarativo** de Kubernetes: describir el estado deseado en vez de dar órdenes paso a paso, y cómo eso permite escalado y actualizaciones sin downtime.
- **Terraform** como infraestructura reproducible — y la disciplina de `destroy` para controlar costos desde el día uno.
- Depuración real de Git: la diferencia entre **ignorar** un archivo, **dejar de rastrearlo** y **limpiarlo del historial** (`git filter-repo`) cuando un binario pesado se cuela por un `.gitignore` mal configurado.

---

## Siguiente fase

Este proyecto es el cimiento sobre el que se monta la capa de IA:

| Fase 1 (esto) | → | Fases siguientes (IA) |
|---|---|---|
| Versionar código | → | Versionar prompts y configuraciones |
| Empaquetar una API | → | Empaquetar un sistema RAG / un agente |
| Probar antes de publicar | → | Evaluar (evals) antes de desplegar |
| Escalar réplicas | → | Escalar inferencia de modelos |
| Levantar una VM | → | Levantar GPUs y bases de datos vectoriales |

---

_Parte de un plan de aprendizaje DevOps enfocado a IA (MLOps / LLMOps)._