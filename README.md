# Impact Realtime Chat (FastAPI + Socket.IO)

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env  # edit if needed (SQLite default)
uvicorn app.main:app --reload --port 8000
