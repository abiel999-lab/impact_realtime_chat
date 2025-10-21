import asyncio
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from .db import SessionLocal
from .config import settings
from . import models


async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

        db: Session = SessionLocal()
        try:
            for a in (
                db.query(models.Attachment)
                .filter(models.Attachment.created_at < cutoff)
                .all()
            ):
                f = os.path.join(settings.upload_dir, a.stored_path)
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass

                db.delete(a)
            db.commit()
        finally:
            db.close()
