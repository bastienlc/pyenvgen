"""Shared test helpers for storage backends."""

from pyenvgen.schema import EnvSchema


def schema(*names: str, internal: set[str] | None = None) -> EnvSchema:
    """Build a minimal EnvSchema for the given variable names."""
    internal = internal or set()
    return EnvSchema.model_validate(
        {
            "variables": {
                name: {
                    "generation": {"rule": "default", "value": "x"},
                    "internal": name in internal,
                }
                for name in names
            }
        }
    )


def values(**kw: str) -> dict:
    """Build a dict of values."""
    return dict(kw)
