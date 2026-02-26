import pytest
import httpx
from app.main import app
from app.db.session import engine
from app.db.base import Base


@pytest.mark.asyncio
async def test_create_ticket_and_user():
    # recreate tables for a clean test DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # create user
        r = await client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
        assert r.status_code == 201
        user = r.json()

        payload = {
            "user_id": user["id"],
            "title": "Bug",
            "description": "Something is broken",
            "tags": ["bug", "urgent"],
        }

        # create ticket
        r2 = await client.post("/tickets/", json=payload)
        assert r2.status_code == 201
        t = r2.json()
        assert t["title"] == "Bug"
        assert t["user_id"] == user["id"]
