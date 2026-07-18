from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "Mi primera API containerizada", "version": "v2"}

@app.get("/salud")
def salud():
    return {"estado": "ok"}