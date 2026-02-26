from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app import crud

router = APIRouter()


@router.get("/", response_model=list[TicketRead])
async def list_tickets(session: AsyncSession = Depends(get_session)):
    return await crud.ticket.list_tickets(session)


@router.post("/", response_model=TicketRead, status_code=201)
async def create_ticket(payload: TicketCreate, session: AsyncSession = Depends(get_session)):
    return await crud.ticket.create_ticket(session, user_id=payload.user_id, title=payload.title, description=payload.description, tags=payload.tags)


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(ticket_id: int, session: AsyncSession = Depends(get_session)):
    ticket = await crud.ticket.get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketRead)
async def patch_ticket(ticket_id: int, payload: TicketUpdate, session: AsyncSession = Depends(get_session)):
    ticket = await crud.ticket.get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return await crud.ticket.update_ticket(session, ticket, title=payload.title, description=payload.description, tags=payload.tags)


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: int, session: AsyncSession = Depends(get_session)):
    ticket = await crud.ticket.get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await crud.ticket.delete_ticket(session, ticket)
    return None
