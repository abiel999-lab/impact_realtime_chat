from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
from .db import get_db
from . import models
from .auth import get_current_user


router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    if db.query(models.Country).count() == 0:
        for c in [
            ("ID", "Indonesia"),
            ("US", "United States"),
            ("MY", "Malaysia"),
            ("SG", "Singapore"),
        ]:
            db.add(models.Country(code=c[0], name=c[1]))
        db.commit()

    return [
        {"code": r.code, "name": r.name}
        for r in db.query(models.Country).order_by(models.Country.name).all()
    ]


@router.get("")
def rooms_by_country(
    code: str = Query(..., min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Room)
        .filter(models.Room.country_code == code.upper())
        .order_by(models.Room.name)
        .all()
    )
    return [{"id": r.id, "name": r.name} for r in rows]


@router.post("/create")
def create_room(
    code: str,
    name: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = code.upper().strip()
    name_norm = name.strip()

    if not name_norm:
        raise HTTPException(status_code=400, detail="Room name required")
    if not db.get(models.Country, code):
        raise HTTPException(status_code=404, detail="Country not found")
    if (
        db.query(models.Room)
        .filter(models.Room.country_code == code, models.Room.name == name_norm)
        .first()
    ):
        raise HTTPException(status_code=409, detail="Room name already exists in this country")

    room = models.Room(
        id=str(uuid.uuid4()),
        name=name_norm,
        country_code=code,
        created_by=user.id,
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return {"id": room.id, "name": room.name}
