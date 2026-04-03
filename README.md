# FDPAC Backend

FastAPI-based backend for the Financial Document Processing and Analysis System (FDPAC).

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/fdpac
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Setup

Run migrations:
```bash
alembic upgrade head
```

## Development

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000)

API documentation available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## API Routes

- `/api/auth` - Authentication endpoints
- `/api/users` - User management
- `/api/records` - Financial records
- `/api/dashboard` - Dashboard data

## Tech Stack

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

## Docker

Build and run with Docker:
```bash
docker build -t fdpac-backend .
docker run -p 8000:8000 --env-file .env fdpac-backend
```