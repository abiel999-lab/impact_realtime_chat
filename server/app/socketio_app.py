import socketio
import jwt
from typing import Dict
from .config import settings


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.sio_cors_origins or "*",
)

sessions: Dict[str, dict] = {}


@sio.event
def connect(sid, environ, auth):
    if auth and auth.get("token"):
        try:
            data = jwt.decode(auth["token"], settings.jwt_secret, algorithms=["HS256"])
            sessions[sid] = {"user_id": int(data["sub"]), "name": ""}
        except Exception:
            pass


@sio.event
async def set_profile(sid, data):
    sess = sessions.get(sid, {})
    sess["name"] = (data or {}).get("name", "anon")
    sessions[sid] = sess


@sio.event
async def join_room(sid, data):
    room_id = (data or {}).get("room_id")
    if not room_id:
        return

    for room in list(await sio.rooms(sid)):
        if room != sid:
            await sio.leave_room(sid, room)

    await sio.enter_room(sid, room_id)
    await sio.emit(
        "user_joined",
        {"username": sessions.get(sid, {}).get("name", "anon"), "room": room_id},
        to=room_id,
    )


@sio.event
async def typing(sid, data):
    room_id = (data or {}).get("room_id")
    await sio.emit(
        "typing",
        {"username": sessions.get(sid, {}).get("name", "anon")},
        to=room_id,
        skip_sid=sid,
    )


@sio.event
async def disconnect(sid):
    name = sessions.get(sid, {}).get("name", "anon")
    try:
        for room in list(await sio.rooms(sid)):
            if room != sid:
                await sio.emit(
                    "user_left",
                    {"username": name, "room": room},
                    to=room,
                )
    except Exception:
        pass

    sessions.pop(sid, None)
