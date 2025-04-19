import os
import sys
# Include project root for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.schemas.user import UserResponse
from src.database.db import get_db
from src.services.auth import auth_service

@pytest.fixture
def mock_user_response():
    """
    Create a UserResponse instance matching the API's response_model.
    """
    return UserResponse(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        avatar="http://example.com/avatar.png",
        confirmed=True,
        created_at=datetime.now(timezone.utc),
        role="user"
    )

@pytest.fixture
def client(mock_user_response):
    """
    TestClient with overridden dependencies:
      - Bypass RateLimiter
      - Mock FastAPILimiter.init
      - Override get_db and auth_service.get_current_user
    """
    from starlette.requests import Request
    # Dummy RateLimiter dependency factory
    def dummy_rate_limiter_factory(*args, **kwargs):
        async def _noop(request: Request, response: None = None):
            return None
        return _noop

    with patch("fastapi_limiter.FastAPILimiter.init", new=AsyncMock()), \
         patch("fastapi_limiter.depends.RateLimiter", new=dummy_rate_limiter_factory), \
         patch("src.routes.users.RateLimiter", new=dummy_rate_limiter_factory):
        from main import app

        async def _get_db_override():
            class DummySession: pass
            return DummySession()

        async def _override_get_current_user():
            return mock_user_response

        app.dependency_overrides[get_db] = _get_db_override
        app.dependency_overrides[auth_service.get_current_user] = _override_get_current_user

        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()


def test_get_current_user(client, mock_user_response):
    """GET /api/users/me returns the current user"""
    response = client.get("/api/users/me")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(mock_user_response.id)
    assert data["username"] == mock_user_response.username
    assert data["email"] == mock_user_response.email
    assert data["avatar"] == mock_user_response.avatar
    assert data["role"] == mock_user_response.role.value

def test_update_avatar(client, mock_user_response, monkeypatch):
    """PATCH /api/users/avatar updates and returns new avatar URL"""
    from src.routes.users import cloudinary, repositories_users
    # Patch Cloudinary upload and image URL builder
    monkeypatch.setattr(cloudinary.uploader, 'upload', MagicMock(return_value={"version": "123"}))
    monkeypatch.setattr(cloudinary.CloudinaryImage, 'build_url', lambda *args, **kwargs: "https://dummy.url/avatar.png")

    # Fake repository update to set avatar on mock_user_response
    async def fake_update_avatar(email, url, db):
        mock_user_response.avatar = url
        return mock_user_response

    monkeypatch.setattr(repositories_users, 'update_avatar_url', fake_update_avatar)

    # Prepare dummy image file
    os.makedirs("tests", exist_ok=True)
    img_path = "tests/test_image.png"
    if not os.path.exists(img_path):
        with open(img_path, "wb") as f:
            # Write minimal valid PNG header
            f.write(b".PNG")

    with open(img_path, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        response = client.patch("/api/users/avatar", files=files)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(mock_user_response.id)
    assert data["avatar"] == "https://dummy.url/avatar.png"
