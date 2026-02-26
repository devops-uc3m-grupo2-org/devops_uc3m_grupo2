from fastapi import FastAPI
from app.api import users, tickets

app = FastAPI(title="Ticket Manager API")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])

@app.get("/health")
async def health():
    return {"status": "ok"}
