from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

from src.database.db import get_db
from src.repository import contacts as crud
from src.schemas.contacts import ContactCreate, ContactUpdate, ContactOut
from src.services.auth import auth_service
from src.entity.models import User
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=ContactOut,dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_contact(
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    contact = await crud.create_contact(db, body, user)
    return contact


@router.get("/", response_model=List[ContactOut])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return await crud.get_contacts(db=db, user=current_user, skip=skip, limit=limit)


@router.get("/{contact_id}", response_model=ContactOut)
async def read_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    contact = await crud.get_contact(db=db, contact_id=contact_id, user=current_user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: UUID,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    contact = await crud.update_contact(db=db, contact_id=contact_id, contact=body, user=current_user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
    ):
    result = await crud.delete_contact(db=db, contact_id=contact_id, user=current_user)
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return


@router.get("/search/", response_model=List[ContactOut])
async def search_contacts(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return await crud.search_contacts(db=db, query=query, user=current_user)


@router.get("/upcoming_birthdays/", response_model=List[ContactOut])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)
    return await crud.get_contacts_with_upcoming_birthdays(
        db=db, start_date=today, end_date=upcoming, user=current_user
    )
