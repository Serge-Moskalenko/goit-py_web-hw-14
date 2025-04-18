from datetime import datetime, timezone
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.entity.models import User
from src.schemas.user import UserSchema
from src.repository import users


class TestUserRepository(IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = AsyncMock()
        self.db.add = MagicMock()
        self.db.commit = AsyncMock()
        self.db.refresh = AsyncMock()

        self.user = User(
            id=uuid4(),
            email="test@example.com",
            password="12345678",
            confirmed=False,
            created_at=datetime.now(timezone.utc),
            refresh_token=None
        )

        self.mock_result = MagicMock()
        self.mock_result.scalar_one_or_none.return_value = self.user

    async def test_get_user_by_email_found(self):
        self.db.execute = AsyncMock(return_value=self.mock_result)
        result = await users.get_user_by_email("test@example.com", self.db)
        self.assertEqual(result, self.user)

    async def test_create_user_success(self):
        body = UserSchema(
            username="tester",
            email="test@example.com",
            password="12345678"
        )
        result = await users.create_user(body, self.db)
        self.assertEqual(result.email, body.email)
        self.db.add.assert_called_once()

    async def test_update_token(self):
        token = "new_refresh_token"
        await users.update_token(self.user, token, self.db)
        self.assertEqual(self.user.refresh_token, token)
        self.db.commit.assert_called_once()

    async def test_confirmed_email(self):
        self.db.execute = AsyncMock(return_value=self.mock_result)
        await users.confirmed_email(self.user.email, self.db)
        self.assertTrue(self.user.confirmed)
        self.db.commit.assert_called_once()

    async def test_update_avatar_url(self):
        self.db.execute = AsyncMock(return_value=self.mock_result)
        new_avatar = "http://example.com/avatar.jpg"
        result = await users.update_avatar_url(self.user.email, new_avatar, self.db)
        self.assertEqual(result.avatar, new_avatar)

    async def test_update_user_password(self):
        self.db.execute = AsyncMock(return_value=self.mock_result)
        await users.update_user_password(self.user.email, "new_pass", self.db)
        self.assertEqual(self.user.password, "new_pass")
