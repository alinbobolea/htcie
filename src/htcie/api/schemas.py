"""API request/response schemas."""

from pydantic import BaseModel

from htcie.core.state import EngineeringState


class EvaluateRequest(BaseModel):
    """Request body for the ``POST /evaluate`` endpoint.

    Attributes:
        state: Fully specified :class:`~htcie.core.state.EngineeringState`
            describing the heat-transfer problem to evaluate.
    """

    state: EngineeringState
