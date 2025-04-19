# 🧰 Fullstack Projects: FastAPI

This repository contains two separate backend projects built using modern Python frameworks:

- `FastApi/` — asynchronous backend with FastAPI, PostgreSQL, Redis, Alembic, Email verification, and JWT authentication


---

## 🚀 FastAPI Project

### 🔧 Setup Instructions

1. **Create a `.env` file inside `FastApi/` with the following variables:**

2. Start the Docker services:

cd FastApi
docker-compose up -d

3. Install dependencies and apply migrations:

poetry install
alembic upgrade head

4. Run the FastAPI app:

poetry run uvicorn src.main:app --reload


## Technologies Used

- Python 3.12
- PostgreSQL 17
- MongoDB (via PyMongo)
- Docker & Docker Compose
- Pydantic Settings for environment configuration
- Sphinx
- Pytest + Unittest