"""Default generation rule – returns a literal value from the schema."""

from __future__ import annotations

from pyenvgen.schema import DefaultGeneration


def generate_default(rule: DefaultGeneration) -> str:
    """Return the literal default value from the schema."""
    return rule.value
