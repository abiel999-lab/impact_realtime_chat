from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os, uuid, aiofiles, asyncio

from .db import get_db
from . import models, schemas
from .config import settings
from .socketio_app import sio  # untuk broadcast event ke room

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/messages", response_model=List[schemas.MessageOut])
def list_messages(
    room: str = Query(default="lobby"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(models.Message).filter(models.Message.room == room).order_by(models.Message.id.desc()).limit(limit)
    items = q.all()
    return list(reversed(items))

@router.post("/messages", response_model=schemas.MessageOut)
def create_message(payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    obj = models.Message(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ---------- NEW: Upload & list attachments ----------
@router.post("/upload", response_model=List[schemas.AttachmentOut])
async def upload_files(
    files: List[UploadFile] = File(...),
    room: str = Form(default="lobby"),
    username: str = Form(default="anon"),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)

    results: List[schemas.AttachmentOut] = []

    # Soft-limit ukuran (per file)
    max_bytes = settings.max_upload_mb * 1024 * 1024

    for f in files:
        # validasi ukuran jika Content-Length tersedia
        # (di beberapa browser tidak reliable; untuk produksi pakai middleware limiter atau proxy)
        # -> kita tetap simpan, tapi bisa tambahkan check manual saat streaming jika ingin.

        # simpan dengan nama aman (UUID) + ekstensi asli
        ext = os.path.splitext(f.filename)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_rel_path = stored_name  # simple; bisa pakai subfolder per tanggal
        stored_abs_path = os.path.join(settings.upload_dir, stored_rel_path)

        size = 0
        try:
            async with aiofiles.open(stored_abs_path, "wb") as out:
                while True:
                    chunk = await f.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        await out.close()
                        os.remove(stored_abs_path)
                        raise HTTPException(status_code=413, detail=f"File too large (> {settings.max_upload_mb} MB)")
                    await out.write(chunk)
        finally:
            await f.close()

        att = models.Attachment(
            room=room,
            username=username,
            original_name=f.filename,
            stored_path=stored_rel_path,
            mime_type=f.content_type or "application/octet-stream",
            size_bytes=size,
        )
        db.add(att)
        db.commit()
        db.refresh(att)

        url = f"/files/{att.stored_path}"
        results.append(
            schemas.AttachmentOut(
                id=att.id, room=att.room, username=att.username,
                original_name=att.original_name, stored_path=att.stored_path,
                mime_type=att.mime_type, size_bytes=att.size_bytes,
                created_at=att.created_at, url=url
            )
        )

        # broadcast ke room via socket
        payload = {
            "id": att.id,
            "room": att.room,
            "username": att.username,
            "original_name": att.original_name,
            "mime_type": att.mime_type,
            "size_bytes": att.size_bytes,
            "url": url,
            "created_at": att.created_at.isoformat(),
        }
        # fire-and-forget
        asyncio.create_task(sio.emit("file_uploaded", payload, to=room))

    return results

@router.get("/attachments", response_model=List[schemas.AttachmentOut])
def list_attachments(
    room: str = Query(default="lobby"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(models.Attachment).filter(models.Attachment.room == room).order_by(models.Attachment.id.desc()).limit(limit)
    items = list(reversed(q.all()))
    # tambah field url
    out: List[schemas.AttachmentOut] = []
    for a in items:
        url = f"/files/{a.stored_path}"
        out.append(
            schemas.AttachmentOut(
                id=a.id, room=a.room, username=a.username,
                original_name=a.original_name, stored_path=a.stored_path,
                mime_type=a.mime_type, size_bytes=a.size_bytes,
                created_at=a.created_at, url=url
            )
        )
    return out
