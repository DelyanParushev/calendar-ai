from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from . import models, schemas, nlp_parser
from .nlp_parser import parse_event_text

app = FastAPI(title="AI Calendar API", version="0.1.0")


# CORS за dev фронтенд
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB init
Base.metadata.create_all(bind=engine)

# Dependency за сесиите

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/parse")
def parse_event(payload: dict):
    text = payload.get("text", "")
    title, dt = parse_event_text(text)

    if not dt:
        return {"error": "Не можах да разбера датата/часа."}

    return {
        "title": title,
        "start": dt.isoformat()
    }


@app.post("/events", response_model=schemas.EventOut)
def create_event(ev: schemas.EventCreate, db: Session = Depends(get_db)):
    obj = models.Event(title=ev.title, start=ev.start, end=ev.end, raw_text=ev.raw_text)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/events", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.start.asc()).all()