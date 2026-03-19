from fastapi import FastAPI, HTTPException, Response
from typing import List

from models import Ticket
from repository import TicketRepository
from service import TicketService


app = FastAPI(title="API de Tickets - Práctica 6")

repo = TicketRepository()
service = TicketService(repo)


@app.post("/tickets", status_code=201, response_model=Ticket)
def post_ticket(ticket: Ticket):
    try:
        return service.crear_ticket(ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tickets", response_model=List[Ticket])
def get_tickets():
    return service.listar_tickets()


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: int):
    t = service.obtener_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return t


@app.put("/tickets/{ticket_id}", response_model=Ticket)
def put_ticket(ticket_id: int, ticket: Ticket):
    updated = service.actualizar_ticket(ticket_id, ticket)
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return updated


@app.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int):
    ok = service.borrar_ticket(ticket_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
