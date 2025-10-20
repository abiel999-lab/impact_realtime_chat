from sqlalchemy import String, Integer, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room: Mapped[str] = mapped_column(String(64), index=True, default="lobby")
    username: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(String(4096))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room: Mapped[str] = mapped_column(String(64), index=True, default="lobby")
    username: Mapped[str] = mapped_column(String(64), index=True)
    original_name: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024), unique=True)  # relative to upload dir
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
