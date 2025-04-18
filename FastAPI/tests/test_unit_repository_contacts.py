from datetime import date
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.repository import contacts
from src.schemas.contacts import ContactCreate
from src.entity.models import Contact, User


class TestContactRepository(IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = MagicMock()
        self.db.execute = AsyncMock()
        self.db.commit = AsyncMock()
        self.db.refresh = AsyncMock()
        self.db.delete = AsyncMock()
        self.user = User(id=uuid4())

    async def test_create_contact_success(self):
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            birthday=date(2000, 1, 1)
        )

        # Setup: no contact with this email
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.db.execute.return_value = mock_result

        self.db.commit.return_value = None
        self.db.refresh.return_value = None

        result = await contacts.create_contact(self.db, contact_data, self.user)

        self.assertEqual(result.email, contact_data.email)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    async def test_get_contacts_returns_list(self):
        fake_contact = Contact(
            id=uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            birthday=date(2000, 1, 1),
            user_id=self.user.id
        )

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fake_contact]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.db.execute.return_value = mock_result

        result = await contacts.get_contacts(self.db, self.user)

        self.assertEqual(result, [fake_contact])
        self.assertEqual(result[0].email, "john@example.com")

    async def test_get_contacts_with_upcoming_birthdays(self):
        fake_contact = Contact(
            id=uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone="9876543210",
            birthday=date(1990, 4, 20),
            user_id=self.user.id
        )

        start = date(1990, 4, 15)
        end = date(1990, 4, 25)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [fake_contact]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.db.execute.return_value = mock_result

        result = await contacts.get_contacts_with_upcoming_birthdays(self.db, start, end, self.user)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_name, "Jane")
