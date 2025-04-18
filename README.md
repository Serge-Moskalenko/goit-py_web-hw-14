# 🧰 Fullstack Projects: FastAPI & Django

This repository contains two separate backend projects built using modern Python frameworks:

- `FastApi/` — asynchronous backend with FastAPI, PostgreSQL, Redis, Alembic, Email verification, and JWT authentication
- `DjangoApp/` — backend with Django (under development)

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

## 🚀 Django Project

- 🔐 User registration and login
- ✍️ Add authors and quotes
- 🔍 Search quotes by tags
- 🧠 Top tags display
- 📧 Password reset via email
- 🐘 PostgreSQL for relational data
- 🍃 MongoDB for quote and author storage
- 🐳 Docker support

## Technologies Used

- Python 3.12
- Django 5.1.7
- PostgreSQL 17
- MongoDB (via PyMongo)
- Docker & Docker Compose
- Pydantic Settings for environment configuration

1. **Create a `.env` file inside `Django/` with the following variables:**

2. Start the Docker services:

cd Django
docker-compose up -d

3. Install dependencies and apply migrations:

poetry install
poetry run python manage.py migrate

4. Run the development server

poetry run python manage.py runserver
##Access the app at http://127.0.0.1:8000/