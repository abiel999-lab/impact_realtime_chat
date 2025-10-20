from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import socketio, os

from .config import settings
from .db import engine, Base
from .routes import router as api_router
from .socketio_app import sio

# Create DB tables
Base.metadata.create_all(bind=engine)

# Ensure upload dir exists
os.makedirs(settings.upload_dir, exist_ok=True)

fastapi_app = FastAPI(title=settings.app_name)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(api_router)

# Static frontend
fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

# Files download (serves uploads)
fastapi_app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")

# Mount Socket.IO
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
