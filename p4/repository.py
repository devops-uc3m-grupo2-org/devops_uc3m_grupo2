from typing import List, Optional
from models import Ticket


class TicketRepository:
    def __init__(self):
        self._db = {}
        self._current_id = 1

    def get_all(self) -> List[Ticket]:
        return list(self._db.values())

    def get(self, id: int) -> Optional[Ticket]:
        return self._db.get(id)

    def save(self, ticket: Ticket) -> Ticket:
        ticket.id = self._current_id
        self._db[self._current_id] = ticket
        self._current_id += 1
        return ticket

    def update(self, id: int, ticket: Ticket) -> Optional[Ticket]:
        if id in self._db:
            ticket.id = id
            self._db[id] = ticket
            return ticket
        return None

    def delete(self, id: int) -> bool:
        return self._db.pop(id, None) is not None
