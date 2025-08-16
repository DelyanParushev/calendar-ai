import json
import random

# Прости шаблони
titles = ["Вечеря", "Среща", "Обяд", "Футбол", "Йога", "Кино", "Концерт"]
people = ["Иван", "Мария", "екипа", "приятели"]
places = ["в парка", "в офиса", "в зала", "в киното"]
days = ["понеделник", "вторник", "сряда", "четвъртък", "петък", "събота", "неделя"]
dates = ["10ти", "12ти", "15ти", "18ти", "20ти", "22ри"]
hours = [str(h) for h in range(7, 23)]

def generate_example():
    # Избира случайно дали датата е ден от седмицата или число
    if random.random() < 0.5:
        when = random.choice(days)
        token_when = "B-WHEN_DAY"
    else:
        when = random.choice(dates)
        token_when = "B-WHEN_DAY"
    
    title = random.choice(titles)
    start_hour = random.choice(hours)
    
    # Случайно добавяне на person и place
    add_person = random.random() < 0.5
    add_place = random.random() < 0.5
    
    tokens = []
    labels = []
    
    # Рандомно редене на изречението
    order = random.choice(["title_first", "when_first"])
    
    if order == "title_first":
        tokens.append(title)
        labels.append("B-TITLE")
        
        tokens.append("от")
        labels.append("O")
        tokens.append(start_hour)
        labels.append("B-WHEN_START")
        
        if when:
            tokens.append(when)
            labels.append(token_when)
    else:
        tokens.append("На" if token_when=="B-WHEN_DAY" and "ти" in when else "")
        if tokens[-1]=="":
            tokens.pop()
        tokens.append(when)
        labels.append(token_when)
        
        tokens.append("от")
        labels.append("O")
        tokens.append(start_hour)
        labels.append("B-WHEN_START")
        
        tokens.append(title)
        labels.append("B-TITLE")
    
    if add_person:
        tokens.append("с")
        labels.append("O")
        tokens.append(random.choice(people))
        labels.append("B-PERSON")
    
    if add_place:
        tokens.append("в")
        labels.append("O")
        tokens.append(random.choice([p.split()[-1] for p in places]))
        labels.append("B-PLACE")
    
    return {"tokens": tokens, "labels": labels}

# Генерираме 200 примера за тренировка
with open("data/train.jsonl", "w", encoding="utf-8") as f:
    for _ in range(200):
        f.write(json.dumps(generate_example(), ensure_ascii=False) + "\n")

# 50 за dev
with open("data/dev.jsonl", "w", encoding="utf-8") as f:
    for _ in range(50):
        f.write(json.dumps(generate_example(), ensure_ascii=False) + "\n")

# 50 за test
with open("data/test.jsonl", "w", encoding="utf-8") as f:
    for _ in range(50):
        f.write(json.dumps(generate_example(), ensure_ascii=False) + "\n")
