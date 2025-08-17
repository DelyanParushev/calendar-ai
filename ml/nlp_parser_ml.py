# ml/nlp_parser_ml.py
import re
import json
from datetime import datetime, timedelta, time, date
from typing import Optional

import torch
from transformers import BertTokenizerFast, BertForTokenClassification

# !!! ВАЖНО: относителният път е спрямо ТЕКУЩАТА РАБОТНА ДИРЕКТОРИЯ
# ако стартираш uvicorn от корена (calendar-ai), това е правилно.
# ако стартираш от backend/, смени на "../ml/model"
MODEL_DIR = "ml/model"

# Зареждане на токенизатор и модел (ТВОЯТ обучен модел)
tokenizer = BertTokenizerFast.from_pretrained(MODEL_DIR)
model = BertForTokenClassification.from_pretrained(MODEL_DIR)
model.eval()

# Зареждане на етикетите от labels.json
with open(f"{MODEL_DIR}/labels.json", encoding="utf-8") as f:
    LABELS = json.load(f)

# Карти за дни от седмицата (на български, lower-case)
WEEKDAYS = {
    "понеделник": 0, "вторник": 1, "сряда": 2, "четвъртък": 3,
    "петък": 4, "събота": 5, "събота.": 5, "неделя": 6, "неделя.": 6
}

# относителни думи
RELATIVE = {
    "днес": 0, "утре": 1, "вдругиден": 2
}

# подсказки за време от деня (ако няма изричен час)
DAYTIME_HINTS = {
    "сутринта": time(9, 0),
    "обед": time(12, 0),
    "наобед": time(12, 0),
    "следобед": time(15, 0),
    "вечерта": time(19, 0),
    "вечер": time(19, 0)
}

def _next_weekday(from_date: date, target_weekday: int) -> date:
    """Връща следващата дата за даден ден от седмицата (>= утре)."""
    days_ahead = (target_weekday - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)

def _parse_day_from_tokens(day_tokens: list[str], now: datetime) -> Optional[date]:
    """Опитва да извлече дата (ден/дата) от токените с WHEN_DAY."""
    if not day_tokens:
        return None

    toks = [t.lower() for t in day_tokens]

    # 1) относителни думи (днес/утре/вдругиден)
    for t in toks:
        if t in RELATIVE:
            return (now + timedelta(days=RELATIVE[t])).date()

    # 2) ден от седмицата
    for t in toks:
        if t in WEEKDAYS:
            return _next_weekday(now.date(), WEEKDAYS[t])

    # 3) дата от типа "20ти", "1ви", "2ри", "7ми", "20", "20."
    for t in toks:
        m = re.match(r"^(\d{1,2})(?:-?(ви|ри|ти|ми))?\.?$", t)
        if m:
            day = int(m.group(1))
            y, mth = now.year, now.month
            try:
                candidate = date(y, mth, day)
            except ValueError:
                if mth == 12:
                    candidate = date(y + 1, 1, day)
                else:
                    candidate = date(y, mth + 1, day)
            if candidate < now.date():
                if candidate.month == 12:
                    candidate = date(candidate.year + 1, 1, candidate.day)
                else:
                    for i in range(1, 3):
                        try:
                            candidate = date(y + (mth + i - 1) // 12,
                                             ((mth + i - 1) % 12) + 1,
                                             day)
                            break
                        except ValueError:
                            continue
            return candidate

    return None

def _parse_time_from_tokens(time_tokens: list[str]) -> Optional[time]:
    """Опитва да извлече час/минути от WHEN_START токени."""
    if not time_tokens:
        return None

    raw = " ".join(time_tokens).lower().strip()
    raw = raw.replace("ч.", "ч").replace("часа", "ч").replace(" часа", "ч").replace(" h", "ч")

    m = re.search(r"\b(\d{1,2})[:\.](\d{1,2})\b", raw)
    if m:
        h, mm = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mm <= 59:
            return time(h, mm)

    m = re.search(r"\b(\d{1,2})\s*ч?\b", raw)
    if m:
        h = int(m.group(1))
        if 0 <= h <= 23:
            return time(h, 0)

    return None

def _find_daytime_hint(tokens: list[str], labels: list[str]) -> Optional[time]:
    """Ако няма WHEN_START, търсим думи като 'сутринта', 'следобед', 'вечерта' в WHEN_DAY токени."""
    for tok, lab in zip(tokens, labels):
        if lab in ("B-WHEN_DAY", "I-WHEN_DAY"):
            if tok.lower() in DAYTIME_HINTS:
                return DAYTIME_HINTS[tok.lower()]
    return None

def parse_text(text: str) -> dict:
    if not text or not text.strip():
        return {"title": "", "datetime": None, "tokens": [], "labels": [], "debug": {"model_dir": MODEL_DIR, "note": "empty text"}}

    words = text.split()
    encoding = tokenizer(words, is_split_into_words=True, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(input_ids=encoding["input_ids"], attention_mask=encoding["attention_mask"])
    logits = outputs.logits
    pred_ids = torch.argmax(logits, dim=-1).squeeze().tolist()

    word_ids = encoding.word_ids(batch_index=0)
    labels = []
    current = None
    for idx, wid in enumerate(word_ids):
        if wid is None:
            continue
        if wid != current:
            current = wid
            label_id = pred_ids[idx]
            labels.append(LABELS[label_id])

    tokens = words
    title_tokens = [t for t, lab in zip(tokens, labels) if lab == "B-TITLE"]
    title = " ".join(title_tokens).strip()

    day_tokens = [t for t, lab in zip(tokens, labels) if lab in ("B-WHEN_DAY", "I-WHEN_DAY")]
    start_tokens = [t for t, lab in zip(tokens, labels) if lab == "B-WHEN_START"]

    now = datetime.now()
    the_date = _parse_day_from_tokens(day_tokens, now)
    the_time = _parse_time_from_tokens(start_tokens)

    if the_time is None:
        the_time = _find_daytime_hint(tokens, labels)

    dt = None
    if the_date and the_time:
        dt = datetime.combine(the_date, the_time)
        if dt < now:
            dt = dt + timedelta(weeks=1)
    elif the_date and not the_time:
        dt = None
    elif not the_date and the_time:
        tentative = datetime.combine(now.date(), the_time)
        if tentative < now:
            tentative += timedelta(days=1)
        dt = tentative

    if not title:
        non_when = [t for t, lab in zip(tokens, labels) if lab not in ("B-WHEN_DAY", "I-WHEN_DAY", "B-WHEN_START")]
        filtered = [t for t in non_when if t.lower() not in {"на", "в", "с", "от"}]
        title = " ".join(filtered).strip()

    return {
        "title": title,
        "datetime": dt,
        "tokens": tokens,
        "labels": labels,
        "debug": {"model_dir": MODEL_DIR, "note": "inference ok"}
    }

if __name__ == "__main__":
    tests = [
        "На 20ти от 21 Разходка",
        "Вечеря от 21 неделя с Гери",
        "Футбол неделя от 19",
        "Среща в офиса в петък 14:30",
        "Покупки в мола в събота следобед",
        "Йога клас утре сутринта",
    ]
    for t in tests:
        res = parse_text(t)
        print(t, "=>", res["title"], res["datetime"])
    print("Loaded model from:", MODEL_DIR)
    print("Tokenizer vocab size:", tokenizer.vocab_size)
    print("Model num labels:", model.config.num_labels)
    print("Labels:", LABELS)