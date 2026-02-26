from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.user import UserCreate, UserRead
from app import crud

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(get_session)):
    users = await crud.user.list_users(session)
    return users


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    return await crud.user.create_user(session, name=payload.name, email=payload.email)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await crud.user.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserCreate, session: AsyncSession = Depends(get_session)):
    user = await crud.user.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud.user.update_user(session, user, name=payload.name, email=payload.email)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await crud.user.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await crud.user.delete_user(session, user)
    return None
