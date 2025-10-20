import socketio
from typing import Dict
from sqlalchemy.orm import Session
from .config import settings
from . import models

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.sio_cors_origins or "*",
)

usernames: Dict[str, str] = {}

@sio.event
async def connect(sid, environ):
    await sio.save_session(sid, {"room": settings.default_room})
    await sio.emit("server_info", {"message": "connected", "sid": sid}, to=sid)

@sio.event
async def set_username(sid, data):
    username = (data or {}).get("username") or f"user-{sid[:5]}"
    usernames[sid] = username
    sess = await sio.get_session(sid)
    room = sess.get("room", settings.default_room)
    await sio.emit("user_joined", {"username": username, "room": room})
    await sio.enter_room(sid, room)

@sio.event
async def join_room(sid, data):
    room = (data or {}).get("room", settings.default_room)
    sess = await sio.get_session(sid)
    prev = sess.get("room", None)
    if prev and prev != room:
        await sio.leave_room(sid, prev)
    sess["room"] = room
    await sio.save_session(sid, sess)
    await sio.enter_room(sid, room)
    await sio.emit("room_changed", {"room": room}, to=sid)

@sio.event
async def typing(sid, data):
    sess = await sio.get_session(sid)
    room = sess.get("room", settings.default_room)
    await sio.emit("typing", {"username": usernames.get(sid, "anon")}, to=room, skip_sid=sid)

@sio.event
async def chat_message(sid, data):
    text = (data or {}).get("text", "").strip()
    if not text:
        return
    sess = await sio.get_session(sid)
    room = (data or {}).get("room") or sess.get("room") or settings.default_room
    username = usernames.get(sid, "anon")

    from .db import SessionLocal
    db: Session = SessionLocal()
    try:
        msg = models.Message(room=room, username=username, text=text)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        payload = {
            "id": msg.id,
            "room": msg.room,
            "username": msg.username,
            "text": msg.text,
            "created_at": msg.created_at.isoformat(),
        }
    finally:
        db.close()

    await sio.emit("chat_message", payload, to=room)

@sio.event
async def disconnect(sid):
    username = usernames.pop(sid, "anon")
    sess = await sio.get_session(sid)
    room = sess.get("room", settings.default_room) if sess else settings.default_room
    await sio.emit("user_left", {"username": username, "room": room})
