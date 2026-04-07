"""GET /methods endpoints — correlation catalog browser."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from htcie.api import dependencies

router = APIRouter(prefix="/methods", tags=["methods"])


@router.get("")
def list_methods(family: str | None = None) -> list[dict]:
    """Return all correlations, optionally filtered by family.

    Query param: ?family=convection_internal
    """
    if family:
        methods = dependencies.registry.by_family(family)
    else:
        methods = dependencies.registry.all()
    return [m.model_dump() for m in methods]


@router.get("/families")
def list_families() -> list[str]:
    """Return sorted list of unique families."""
    return dependencies.registry.families()


@router.get("/{key:path}")
def get_method(key: str) -> dict:
    """Return full metadata for one correlation by key.

    Key format: e.g. internal.gnielinski (note: dots, not slashes)
    """
    try:
        return dependencies.registry.get(key).model_dump()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Method '{key}' not found")
