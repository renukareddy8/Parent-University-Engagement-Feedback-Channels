import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_submit_and_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        payload = {
            "parent_name": "Jane Doe",
            "student_name": "Alice",
            "student_id": "S12345",
            "title": "Dining concerns",
            "contact": "jane@example.com",
            "text": "The cafeteria food is often cold and the library hours are too short.",
        }
        r = await ac.post("/api/feedback", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "category" in data
        assert "sentiment" in data
        assert "department" in data
        assert "notified" in data

        r2 = await ac.get("/api/feedbacks")
        assert r2.status_code == 200
        arr = r2.json()
        assert isinstance(arr, list)
        assert any(item.get("id") == data.get("id") for item in arr)
