from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import socketio
import os
import asyncio
from .config import settings
from .db import engine, Base
from .routes_auth import router as auth_router
from .routes_rooms import router as rooms_router
from .routes_chat import router as chat_router
from .socketio_app import sio
from .tasks import cleanup_loop


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI app
fastapi_app = FastAPI(title=settings.app_name)

# Configure CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
fastapi_app.include_router(auth_router)
fastapi_app.include_router(rooms_router)
fastapi_app.include_router(chat_router)

# Serve static files for uploads
os.makedirs(settings.upload_dir, exist_ok=True)
fastapi_app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")


# Background cleanup task on startup
@fastapi_app.on_event("startup")
async def _startup():
    asyncio.create_task(cleanup_loop())


# Combine FastAPI and Socket.IO ASGI apps
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
