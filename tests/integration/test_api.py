"""API pagination, filtering, health and OpenAPI tests."""

from __future__ import annotations

import pytest
from app.core.enums import RunTrigger
from app.services.pipeline import OpportunityPipeline
from app.sources.demo_dataset import write_demo_files
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient) -> None:
    live = await client.get("/health")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"


@pytest.mark.asyncio
async def test_openapi_metadata(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"].startswith("Opportunity")
    assert "opportunities" in {tag["name"] for tag in payload["tags"]}


@pytest.mark.asyncio
async def test_pagination_and_filtering(client: AsyncClient, db_session: AsyncSession) -> None:
    write_demo_files()
    pipeline = OpportunityPipeline(db_session)
    await pipeline.run(
        source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
    )
    await db_session.commit()

    page = await client.get("/api/v1/opportunities", params={"page": 1, "page_size": 10})
    assert page.status_code == 200
    body = page.json()
    assert body["page_size"] == 10
    assert body["total"] > 10
    assert len(body["items"]) == 10

    filtered = await client.get("/api/v1/opportunities", params={"min_score": 70, "page_size": 50})
    assert filtered.status_code == 200
    for item in filtered.json()["items"]:
        assert item["score"] >= 70

    keyword = await client.get(
        "/api/v1/opportunities", params={"keyword": "Python", "page_size": 20}
    )
    assert keyword.status_code == 200
    assert keyword.json()["total"] >= 1

    top = await client.get("/api/v1/opportunities/top")
    assert top.status_code == 200
    assert isinstance(top.json(), list)

    detail_id = page.json()["items"][0]["id"]
    detail = await client.get(f"/api/v1/opportunities/{detail_id}")
    assert detail.status_code == 200
    assert "score_reasons" in detail.json()
