from fastapi import FastAPI
from backend.database import engine,Base
from routes import ingest, csi, auth
app = FastAPI(title="SafeMinds Backend API")

Base.metadata.create_all(bind=engine)

app.include_router(ingest.router)
app.include_router(auth.router)
app.include_router(csi.router)


@app.get("/")
def home():
    return {
        "message": "SafeMinds backend is running"
    }