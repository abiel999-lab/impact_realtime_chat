from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os, uuid, aiofiles

from .db import get_db
from . import models
from .auth import RegisterIn, LoginIn, UserOut, hash_password, verify_password, create_token, get_current_user
from .config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=payload.email,
        name=payload.name,
        gender=payload.gender or "unspecified",
        password_hash=hash_password(payload.password),
        avatar_filename="",
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_token(user.id)
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "gender": user.gender, "avatar_url": avatar_url(user)}}

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id)
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "gender": user.gender, "avatar_url": avatar_url(user)}}

@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "gender": user.gender, "avatar_url": avatar_url(user)}

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    os.makedirs(os.path.join(settings.upload_dir, "avatars"), exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    name = f"u{user.id}_{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(settings.upload_dir, "avatars", name)

    async with aiofiles.open(abs_path, "wb") as out:
        content = await file.read()
        await out.write(content)
    user.avatar_filename = f"avatars/{name}"
    db.add(user); db.commit(); db.refresh(user)
    return {"avatar_url": avatar_url(user)}

def avatar_url(user: models.User) -> str:
    if user.avatar_filename:
        return f"/files/{user.avatar_filename}"
    # fallback default by gender
    if (user.gender or "").lower().startswith("f"):
        return "/static/avatars/avatar_female.png"
    return "/static/avatars/avatar_male.png"