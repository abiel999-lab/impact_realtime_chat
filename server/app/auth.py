import datetime as dt
import jwt
from passlib.hash import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from .config import settings
from .db import get_db
from . import models


class RegisterIn(BaseModel):
    email: EmailStr
    name: str
    password: str
    gender: str | None = "unspecified"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def hash_password(pw: str) -> str:
    return bcrypt.hash(pw)


def verify_password(pw: str, h: str) -> bool:
    return bcrypt.verify(pw, h)


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=settings.jwt_expire_minutes),
        "iat": dt.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
):
    if not creds:
        raise HTTPException(status_code=401, detail="No token")

    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(data["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
