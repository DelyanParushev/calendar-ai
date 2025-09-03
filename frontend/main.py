# backend/main.py
from datetime import datetime, timedelta
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
    dt = result.get("datetime") or result.get("start")  # Backwards compatibility
    if dt is None:
        return {
            "error": "Не можах да разбера датата/часа.",
            "debug": {
                "tokens": result.get("tokens", []),
                "labels": result.get("labels", []),
                **(result.get("debug") or {})
            }
        }

    end = result.get("end_datetime")  # Get the end time from parse_text
    # If no end time is specified, set it to start time + 1 hour
    if not end and dt:
        end = dt + timedelta(hours=1)
        
    return {
        "title": result.get("title", ""),
        "start": dt.isoformat(),
        "end": end.isoformat() if end else None,
        "tokens": result.get("tokens", []),
        "labels": result.get("labels", []),
        "debug": result.get("debug", {})
    }

@app.post("/events", response_model=schemas.EventOut)
def create_event(payload: dict, db: Session = Depends(get_db)):
    # Check if we have pre-parsed data
    if "title" in payload and "start" in payload:
        # Use pre-parsed data from frontend
        start = datetime.fromisoformat(payload["start"])
        # If end time is not specified, set it to start time + 1 hour
        end = datetime.fromisoformat(payload["end"]) if payload.get("end") else (start + timedelta(hours=1))
        
        obj = models.Event(
            title=payload["title"],
            start=start,
            end=end,
            raw_text=payload.get("raw_text")
        )
    else:
        # Parse from raw text
        text = payload.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Не е подаден текст.")

        result = parse_text(text)
        title = result.get("title", "")
        dt = result.get("datetime") or result.get("start")  # Backwards compatibility
        if dt is None:
            raise HTTPException(status_code=400, detail="Не можах да разбера датата/часа.")
            
        end = result.get("end_datetime")
        if not end:
            end = dt + timedelta(hours=1)

        obj = models.Event(title=title, start=dt, end=end, raw_text=text)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/events", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.start.asc()).all()

@app.delete("/events/{event_id}", response_model=schemas.EventOut)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Събитието не е намерено")
    db.delete(event)
    db.commit()
    return event
