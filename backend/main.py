# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from . import models, schemas
from ml.nlp_parser_ml import parse_text

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/parse")
def parse_event(payload: dict):
    text = payload.get("text", "")
    if not text:
        return {"error": "Не е подаден текст."}

    result = parse_text(text)
    dt = result.get("datetime")
    if dt is None:
        return {
            "error": "Не можах да разбера датата/часа.",
            "debug": {
                "tokens": result.get("tokens", []),
                "labels": result.get("labels", []),
                **(result.get("debug") or {})
            }
        }

    return {
        "title": result.get("title", ""),
        "start": dt.isoformat(),
        "tokens": result.get("tokens", []),
        "labels": result.get("labels", []),
        "debug": result.get("debug", {})
    }

@app.post("/events", response_model=schemas.EventOut)
def create_event_from_text(payload: dict, db: Session = Depends(get_db)):
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Не е подаден текст.")

    result = parse_text(text)
    title = result.get("title", "")
    dt = result.get("datetime")
    if dt is None:
        raise HTTPException(status_code=400, detail="Не можах да разбера датата/часа.")

    obj = models.Event(title=title, start=dt, end=None, raw_text=text)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/events", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.start.asc()).all()
