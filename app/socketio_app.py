import socketio
from typing import Dict
import jwt
from .config import settings

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.sio_cors_origins or "*",
)

# sid -> {user_id, name, room_id}
sessions: Dict[str, dict] = {}

@sio.event
def connect(sid, environ, auth):
    """
    Client should pass: io({ auth: { token: '...' } })
    """
    user = None
    if auth and auth.get("token"):
        try:
            data = jwt.decode(auth["token"], settings.jwt_secret, algorithms=["HS256"])
            user_id = int(data["sub"])  # not fetching DB here for speed; chat API uses token again
            sessions[sid] = {"user_id": user_id, "name": ""}
        except Exception:
            pass
    sio.start_background_task(lambda: None)

@sio.event
async def set_profile(sid, data):
    # set display name for socket session (optional)
    name = (data or {}).get("name", "")
    sess = sessions.get(sid, {})
    sess["name"] = name
    sessions[sid] = sess
    await sio.emit("server_info", {"message": "connected", "sid": sid}, to=sid)

@sio.event
async def join_room(sid, data):
    room_id = (data or {}).get("room_id")
    if not room_id:
        return
    # leave previous
    for room in list(await sio.rooms(sid)):
        if room != sid:  # skip private room
            await sio.leave_room(sid, room)
    await sio.enter_room(sid, room_id)
    name = sessions.get(sid, {}).get("name", "anon")
    await sio.emit("user_joined", {"username": name, "room": room_id}, to=room_id)

@sio.event
async def typing(sid, data):
    room_id = (data or {}).get("room_id")
    await sio.emit("typing", {"username": sessions.get(sid, {}).get("name", "anon")}, to=room_id, skip_sid=sid)

@sio.event
async def disconnect(sid):
    name = sessions.get(sid, {}).get("name", "anon")
    # broadcast to all rooms this sid was in
    try:
        for room in list(await sio.rooms(sid)):
            if room != sid:
                await sio.emit("user_left", {"username": name, "room": room})
    except Exception:
        pass
    sessions.pop(sid, None)