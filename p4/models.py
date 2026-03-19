from pydantic import BaseModel, Field
from typing import List, Optional


class Ticket(BaseModel):
    id: Optional[int] = None
    titulo: str
    descripcion: str
    creador: str
    etiquetas: List[str] = Field(default_factory=list)
