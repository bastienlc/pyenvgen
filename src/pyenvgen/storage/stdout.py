"""Stdout storage backend – print environment variables to standard output."""

from __future__ import annotations

from typing import Any

from pyenvgen.schema import EnvSchema


class StdoutStorage:
    """Print environment variables to standard output."""

    def load(self) -> dict[str, str]:
        """No existing values to load from stdout."""
        return {}

    def store(
        self,
        values: dict[str, Any],
        schema: EnvSchema,
    ) -> None:
        from pyenvgen.storage import _public_values

        for name, value in _public_values(values, schema).items():
            print(f"{name}={value}")
