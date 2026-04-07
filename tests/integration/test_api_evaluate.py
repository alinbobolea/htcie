"""Integration tests for the POST /evaluate and GET /methods endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from htcie.api import dependencies
from htcie.api.main import app
from htcie.core.loader import build_registry


@pytest.fixture(scope="module", autouse=True)
def preload_registry() -> None:
    """Seed the shared registry singleton before any tests in this module run.

    The FastAPI lifespan event only fires when the ASGI server starts; during
    httpx async transport tests the lifespan is not triggered automatically, so
    we populate the registry directly here.
    """
    if not dependencies.registry.all():
        dependencies.registry = build_registry()


_INTERNAL_PAYLOAD = {
    "state": {
        "fluid": {
            "density": 1.2,
            "viscosity": 1.813e-5,
            "thermal_conductivity": 0.026,
            "heat_capacity": 1005.0,
        },
        "geometry": {
            "geometry_type": "circular_tube",
            "characteristic_length": 0.02,
            "hydraulic_diameter": 0.02,
        },
        "boundary": {
            "boundary_type": "constant_wall_temperature",
        },
        "flow": {
            "velocity": 10.0,
        },
    }
}


@pytest.mark.anyio
async def test_evaluate_valid_internal_returns_200_with_expected_keys() -> None:
    """POST /evaluate with valid internal convection input returns 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/evaluate", json=_INTERNAL_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert "ranking" in body, (
        f"'ranking' key missing from response: {list(body.keys())}"
    )
    assert "confidence" in body, "'confidence' key missing from response"
    assert "explanation" in body, "'explanation' key missing from response"


@pytest.mark.anyio
async def test_evaluate_ranking_contains_scored_methods() -> None:
    """POST /evaluate ranking list must be non-empty with key and score fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/evaluate", json=_INTERNAL_PAYLOAD)

    assert response.status_code == 200
    ranking = response.json()["ranking"]
    assert len(ranking) > 0
    first = ranking[0]
    assert "key" in first
    assert "score" in first


@pytest.mark.anyio
async def test_evaluate_invalid_payload_returns_422() -> None:
    """POST /evaluate with missing required fields must return 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/evaluate", json={"state": {}})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_methods_returns_200_with_sufficient_entries() -> None:
    """GET /methods must return 200 with at least 11 correlation entries."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/methods")

    assert response.status_code == 200
    methods = response.json()
    assert len(methods) >= 11, f"Expected ≥ 11 methods, got {len(methods)}"


@pytest.mark.anyio
async def test_list_methods_entries_have_key_field() -> None:
    """Each entry returned by GET /methods must contain a 'key' field."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/methods")

    assert response.status_code == 200
    for entry in response.json():
        assert "key" in entry, f"Entry missing 'key' field: {entry}"


@pytest.mark.anyio
async def test_get_single_method_gnielinski_returns_200_with_key() -> None:
    """GET /methods/internal.gnielinski must return 200 with a 'key' field."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/methods/internal.gnielinski")

    assert response.status_code == 200
    body = response.json()
    assert body["key"] == "internal.gnielinski"


@pytest.mark.anyio
async def test_get_unknown_method_returns_404() -> None:
    """GET /methods/<unknown> must return 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/methods/internal.nonexistent_correlation")

    assert response.status_code == 404
