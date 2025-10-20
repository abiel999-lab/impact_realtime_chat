import asyncio
from datetime import datetime, timedelta, timezone
import os
from sqlalchemy.orm import Session
from .db import SessionLocal
from .config import settings
from . import models

async def cleanup_loop():
    while True:
        try:
            await asyncio.sleep(60)  # every minute
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
            db: Session = SessionLocal()
            try:
                q = db.query(models.Attachment).filter(models.Attachment.created_at < cutoff)
                for a in q.all():
                    abs_path = os.path.join(settings.upload_dir, a.stored_path)
                    try:
                        if os.path.exists(abs_path):
                            os.remove(abs_path)
                    except Exception:
                        pass
                    db.delete(a)
                db.commit()
            finally:
                db.close()
        except Exception:
            # never crash
            await asyncio.sleep(5)