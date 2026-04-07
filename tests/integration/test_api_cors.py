"""Tests for CORS configuration on the htcie FastAPI application."""

from __future__ import annotations

from fastapi.testclient import TestClient

from htcie.api.main import app


def test_cors_header_present_on_simple_get() -> None:
    """API includes CORS allow-all header when Origin header is present."""
    client = TestClient(app)
    response = client.get(
        "/health", headers={"Origin": "https://htcie-gui.onrender.com"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_preflight_returns_200() -> None:
    """OPTIONS preflight for POST /evaluate is allowed from any origin."""
    client = TestClient(app)
    response = client.options(
        "/evaluate",
        headers={
            "Origin": "https://htcie-gui.onrender.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
    assert response.headers.get("access-control-allow-methods") is not None
