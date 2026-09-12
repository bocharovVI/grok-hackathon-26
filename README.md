# Medical History API

Stack: FastAPI + PostgreSQL + SQLAlchemy.

## Quick start

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Registration

`POST /auth/register`

Required: `email`, `password`, `first_name`, `last_name`.  
Optional: `phone_number`, `date_of_birth`, `height`, `blood_type`.
