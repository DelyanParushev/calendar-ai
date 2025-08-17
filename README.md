# AI Calendar – Backend MVP

## ML модела не е качен тук, понеже е над 4.5GB до момента. Очаквам да стане още по-голям понеже има неща, които трябва да се доизпипат.
```bash
Да обуча модела с допълнителни примери като:
Text: Йога клас утре сутринта
Title: Йога
Datetime: 2025-08-18 09:00:00
Tokens: ['Йога', 'клас', 'утре', 'сутринта']
Labels: ['B-TITLE', 'B-TITLE', 'B-WHEN_DAY', 'B-WHEN_DAY']

## Инсталация и старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# start backend
# uvicorn backend.main:app --reload

# start fronend
# cd frontend
# npm run dev