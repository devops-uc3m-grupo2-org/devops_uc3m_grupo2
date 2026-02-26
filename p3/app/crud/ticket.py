from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.ticket import Ticket
from app.models.user import User


async def get_ticket(session: AsyncSession, ticket_id: int) -> Ticket | None:
    return await session.get(Ticket, ticket_id)


async def list_tickets(session: AsyncSession) -> list[Ticket]:
    q = await session.execute(select(Ticket))
    return q.scalars().all()


async def create_ticket(session: AsyncSession, user_id: int, title: str, description: str, tags: list[str]) -> Ticket:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ticket = Ticket(user_id=user_id, title=title, description=description, tags=tags)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def delete_ticket(session: AsyncSession, ticket: Ticket) -> None:
    await session.delete(ticket)
    await session.commit()


async def update_ticket(session: AsyncSession, ticket: Ticket, title: str | None, description: str | None, tags: list[str] | None) -> Ticket:
    if title is not None:
        ticket.title = title
    if description is not None:
        ticket.description = description
    if tags is not None:
        ticket.tags = tags
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket
