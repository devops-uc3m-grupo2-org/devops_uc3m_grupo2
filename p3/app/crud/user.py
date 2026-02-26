from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.user import User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def list_users(session: AsyncSession) -> list[User]:
    q = await session.execute(select(User))
    return q.scalars().all()


async def create_user(session: AsyncSession, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()


async def update_user(session: AsyncSession, user: User, name: str | None, email: str | None) -> User:
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return user
