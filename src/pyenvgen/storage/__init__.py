"""Storage module – writes generated environment variables to outputs.

Each storage backend implements the ``store`` protocol: it receives the
final dict of key-value pairs and writes them to the target.
"""

from __future__ import annotations

from typing import Any, Protocol

from pyenvgen.schema import EnvSchema


class StorageBackend(Protocol):
    """Protocol that all storage backends must satisfy."""

    def store(
        self,
        values: dict[str, Any],
        schema: EnvSchema,
    ) -> None: ...


class StdoutStorage:
    """Print environment variables to standard output."""

    def store(
        self,
        values: dict[str, Any],
        schema: EnvSchema,
    ) -> None:
        for name, value in values.items():
            var_schema = schema.variables[name]
            if var_schema.internal:
                continue
            print(f"{name}={value}")


def get_storage(backend: str) -> StorageBackend:
    """Return the storage backend for the given name."""
    backends: dict[str, StorageBackend] = {
        "stdout": StdoutStorage(),
    }

    if backend not in backends:
        raise ValueError(
            f"Unknown storage backend '{backend}'. Available: {', '.join(backends)}"
        )

    return backends[backend]
