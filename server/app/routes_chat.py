from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import aiofiles
import asyncio
from datetime import datetime, timedelta, timezone
from .db import get_db
from . import models
from .auth import get_current_user
from .config import settings
from .socketio_app import sio


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/messages")
def list_messages(
    room_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(models.Message.id.desc())
        .limit(limit)
    )
    return list(
        reversed(
            [
                {
                    "id": m.id,
                    "room_id": m.room_id,
                    "username": m.username,
                    "text": m.text,
                    "created_at": m.created_at,
                }
                for m in q.all()
            ]
        )
    )


@router.post("/message")
def create_message(
    room_id: str = Form(...),
    text: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = models.Message(room_id=room_id, user_id=user.id, username=user.name, text=text)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    payload = {
        "id": msg.id,
        "room_id": room_id,
        "username": user.name,
        "text": msg.text,
        "created_at": msg.created_at.isoformat(),
    }

    asyncio.create_task(sio.emit("chat_message", payload, to=room_id))
    return payload


@router.post("/upload")
async def upload_files(
    room_id: str = Form(...),
    files: List[UploadFile] = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)
    room_dir = os.path.join(settings.upload_dir, room_id)
    os.makedirs(room_dir, exist_ok=True)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    outs = []

    for f in files:
        ext = os.path.splitext(f.filename)[1]
        name = f"{uuid.uuid4().hex}{ext}"
        rel_path = os.path.join(room_id, name).replace("\\", "/")
        abs_path = os.path.join(settings.upload_dir, rel_path)
        size = 0

        try:
            async with aiofiles.open(abs_path, "wb") as out:
                while True:
                    chunk = await f.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        await out.close()
                        os.remove(abs_path)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large (> {settings.max_upload_mb} MB)",
                        )
                    await out.write(chunk)
        finally:
            await f.close()

        att = models.Attachment(
            room_id=room_id,
            user_id=user.id,
            username=user.name,
            original_name=f.filename,
            stored_path=rel_path,
            mime_type=f.content_type or "application/octet-stream",
            size_bytes=size,
        )

        db.add(att)
        db.commit()
        db.refresh(att)

        url = f"/files/{rel_path}"
        payload = {
            "id": att.id,
            "room_id": room_id,
            "username": user.name,
            "original_name": att.original_name,
            "mime_type": att.mime_type,
            "size_bytes": att.size_bytes,
            "url": url,
            "created_at": att.created_at.isoformat(),
        }

        outs.append(payload)
        asyncio.create_task(sio.emit("file_uploaded", payload, to=room_id))

    return outs


@router.get("/attachments")
def list_attachments(
    room_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Attachment)
        .filter(models.Attachment.room_id == room_id)
        .order_by(models.Attachment.id.desc())
        .limit(limit)
    )
    return list(
        reversed(
            [
                {
                    "id": a.id,
                    "room_id": a.room_id,
                    "username": a.username,
                    "original_name": a.original_name,
                    "mime_type": a.mime_type,
                    "size_bytes": a.size_bytes,
                    "url": f"/files/{a.stored_path}",
                    "created_at": a.created_at,
                }
                for a in q.all()
            ]
        )
    )


@router.delete("/attachments/expired")
def delete_expired(db: Session = Depends(get_db)):
    db.commit()
    return {"removed": removed}
