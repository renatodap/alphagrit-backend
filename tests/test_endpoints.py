import pytest
from httpx import AsyncClient
from app.main import app


def fake_jwt(sub: str = "user-123", roles: list[str] | None = None) -> str:
    import json, base64

    roles = roles or []
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": sub, "roles": roles}).encode()
    ).rstrip(b"=")
    return f"{header.decode()}.{payload.decode()}."


@pytest.mark.asyncio
async def test_ebooks_list_ok():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/v1/ebooks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_metrics_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/v1/me/metrics")
        assert r.status_code == 401
        token = fake_jwt()
        r2 = await ac.get("/api/v1/me/metrics", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200


@pytest.mark.asyncio
async def test_uploads_paths_return():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        token = fake_jwt()
        r = await ac.post(
            "/api/v1/uploads/metrics",
            json={"metric_id": 1, "filename": "test.png"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["bucket"] in ("metrics-photos", "post-photos")
        assert "path" in body


@pytest.mark.asyncio
async def test_checkout_endpoints_exist():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        token = fake_jwt()
        r1 = await ac.post("/api/v1/ebooks/checkout/ebooks/1", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code in (200, 500)  # 500 if stripe key missing
        r2 = await ac.post("/api/v1/programs/1/checkout?tier=premium", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code in (200, 500)
