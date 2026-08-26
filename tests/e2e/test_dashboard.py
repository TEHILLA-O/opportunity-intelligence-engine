"""Dashboard HTML smoke test."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_renders(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert b"Opportunity Intelligence" in response.content
