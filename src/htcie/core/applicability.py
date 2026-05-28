"""Deterministic applicability logic for correlation candidates."""

from __future__ import annotations

from dataclasses import dataclass, field

from htcie.core.registry import CorrelationMetadata
from htcie.core.state import EngineeringState


@dataclass(slots=True)
class ApplicabilityResult:
    """Outcome of an applicability check over a set of correlations.

    Attributes:
        applicable: Correlations whose validity rules are satisfied by the
            current :class:`~htcie.core.state.EngineeringState`.
        excluded: Pairs of ``(metadata, reason)`` for correlations that were
            rejected, with a human-readable explanation of the first failing
            check.
    """

    applicable: list[CorrelationMetadata] = field(default_factory=list)
    excluded: list[tuple[CorrelationMetadata, str]] = field(default_factory=list)


class ApplicabilityEngine:
    """Filters a list of correlation candidates against an engineering state.

    Each correlation's ``validity`` dict is checked in order: geometry type,
    then :math:`Re` bounds, then :math:`Pr` bounds. The first failing check
    determines the exclusion reason; subsequent checks are not evaluated.
    """

    def evaluate(
        self, state: EngineeringState, methods: list[CorrelationMetadata]
    ) -> ApplicabilityResult:
        """Check every method in *methods* and return an :class:`ApplicabilityResult`.

        Args:
            state: Current engineering state providing :math:`Re`, :math:`Pr`,
                and geometry type.
            methods: Candidate correlations to evaluate (typically
                ``registry.all()``).

        Returns:
            :class:`ApplicabilityResult` with ``applicable`` and ``excluded``
            lists populated.
        """
        result = ApplicabilityResult()
        for method in methods:
            reason = self._check(method, state)
            if reason is None:
                result.applicable.append(method)
            else:
                result.excluded.append((method, reason))
        return result

    def _check(
        self, method: CorrelationMetadata, state: EngineeringState
    ) -> str | None:
        """Return an exclusion reason string, or ``None`` if the method is
        applicable."""
        validity = method.validity
        re_min = validity.get("re_min")
        re_max = validity.get("re_max")
        pr_min = validity.get("pr_min")
        pr_max = validity.get("pr_max")
        geometry = validity.get("geometry_type")

        if geometry and geometry != state.geometry.geometry_type:
            return (
                f"Geometry type {state.geometry.geometry_type!r} does not match"
                f" required {geometry!r}."
            )
        if re_min is not None and state.reynolds < re_min:
            return f"Reynolds number {state.reynolds:.3g} is below minimum {re_min}."
        if re_max is not None and state.reynolds > re_max:
            return f"Reynolds number {state.reynolds:.3g} is above maximum {re_max}."
        if pr_min is not None and state.prandtl < pr_min:
            return f"Prandtl number {state.prandtl:.3g} is below minimum {pr_min}."
        if pr_max is not None and state.prandtl > pr_max:
            return f"Prandtl number {state.prandtl:.3g} is above maximum {pr_max}."

        # L/D entry-length check: enforced when developing_length is provided.
        ld_min = validity.get("ld_min")
        if (
            ld_min is not None
            and state.entry_length_ratio is not None
            and state.entry_length_ratio < ld_min
        ):
            return (
                f"L/D ratio {state.entry_length_ratio:.1f} is below minimum {ld_min}"
                " (thermally developing flow)."
            )

        # TODO: enforce n_rows_min once EngineeringState gains an n_rows field.
        # n_rows_min is present in tube_bank YAML validity dicts (e.g. 20 for
        # Žukauskas bank) but cannot be checked without the row count in state.

        return None
