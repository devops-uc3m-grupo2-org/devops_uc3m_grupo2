from typing import List, Optional
from models import Ticket
from repository import TicketRepository


class TicketService:
    def __init__(self, repository: TicketRepository):
        self.repository = repository

    def crear_ticket(self, ticket: Ticket) -> Ticket:
        if not ticket.etiquetas:
            raise ValueError("Un ticket debe tener al menos una etiqueta")
        ticket.titulo = ticket.titulo.upper()
        return self.repository.save(ticket)

    def listar_tickets(self) -> List[Ticket]:
        return self.repository.get_all()

    def obtener_ticket(self, id: int) -> Optional[Ticket]:
        return self.repository.get(id)

    def actualizar_ticket(self, id: int, ticket: Ticket) -> Optional[Ticket]:
        return self.repository.update(id, ticket)

    def borrar_ticket(self, id: int) -> bool:
        return self.repository.delete(id)
