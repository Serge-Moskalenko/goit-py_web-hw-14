from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from src.entity.models import Contact, User
from src.schemas.contacts import ContactCreate


async def create_contact(
    db: AsyncSession, contact: ContactCreate, user: User
) -> Contact:
    stmt = select(Contact).filter(Contact.email == contact.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_contact = Contact(**contact.model_dump(), user_id=user.id)
    db.add(new_contact)
    try:
        await db.commit()
        await db.refresh(new_contact)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Failed to create contact. Integrity error."
        )

    return new_contact


async def get_contacts(
    db: AsyncSession, user: User, skip: int = 0, limit: int = 100
) -> List[Contact]:
    stmt = select(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contact(db: AsyncSession, contact_id: UUID, user: User) -> Contact | None:
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_contact(
    db: AsyncSession, contact_id: UUID, contact: ContactCreate, user: User
) -> Contact | None:
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    db_contact = result.scalar_one_or_none()
    if db_contact:
        for field, value in contact.model_dump().items():
            setattr(db_contact, field, value)
        await db.commit()
        await db.refresh(db_contact)
    return db_contact


async def delete_contact(db: AsyncSession, contact_id: UUID, user: User) -> dict:
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    db_contact = result.scalar_one_or_none()
    if db_contact:
        await db.delete(db_contact)
        await db.commit()
        return {"ok": True}
    return {"ok": False, "error": "Not found"}


async def search_contacts(db: AsyncSession, query: str, user: User) -> List[Contact]:
    stmt = select(Contact).filter(
        Contact.first_name.ilike(f"%{query}%")
        | Contact.last_name.ilike(f"%{query}%")
        | Contact.email.ilike(f"%{query}%"),
        user=user,
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contacts_with_upcoming_birthdays(
    db: AsyncSession, start_date: date, end_date: date, user: User
) -> List[Contact]:
    stmt = select(Contact).filter(
        Contact.user_id == user.id, Contact.birthday.between(start_date, end_date)
    )

    result = await db.execute(stmt)
    return result.scalars().all()
