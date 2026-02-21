"""Storage module – writes generated environment variables to outputs.

Each storage backend implements the ``store`` protocol: it receives the
final dict of key-value pairs and writes them to the target.

File-based backends perform *non-destructive* updates: they preserve all
existing content (comments, unrelated keys, blank lines) and only update or
append the variables that are managed by pyenvgen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from pyenvgen.schema import EnvSchema
from pyenvgen.storage.dotenv import DotEnvStorage
from pyenvgen.storage.json import JsonStorage
from pyenvgen.storage.stdout import StdoutStorage
from pyenvgen.storage.toml import TomlStorage
from pyenvgen.storage.yaml import YamlStorage


class StorageBackend(Protocol):
    """Protocol that all storage backends must satisfy."""

    def load(self) -> dict[str, str]: ...

    def store(
        self,
        values: dict[str, Any],
        schema: EnvSchema,
    ) -> None: ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _public_values(values: dict[str, Any], schema: EnvSchema) -> dict[str, Any]:
    """Return only the non-internal variables as strings."""
    return {
        name: str(value)
        for name, value in values.items()
        if not schema.variables[name].internal
    }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_FILE_EXTENSIONS: dict[str, type] = {
    ".env": DotEnvStorage,
    ".json": JsonStorage,
    ".toml": TomlStorage,
    ".yaml": YamlStorage,
    ".yml": YamlStorage,
}


def get_storage(backend: str) -> StorageBackend:
    """Return the storage backend for the given name or file path.

    Pass ``"stdout"`` to print to standard output, or a file path whose
    extension determines the format (``*.env``, ``*.json``, ``*.toml``,
    ``*.yaml`` / ``*.yml``).
    """
    if backend == "stdout":
        return StdoutStorage()

    path = Path(backend)

    # Match on the full filename for dotenv files (e.g. ".env", ".env.local")
    # before falling back to the suffix.
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return DotEnvStorage(path)

    suffix = path.suffix.lower()
    if suffix in _FILE_EXTENSIONS:
        return _FILE_EXTENSIONS[suffix](path)

    raise ValueError(
        f"Cannot determine storage format for '{backend}'. "
        f"Pass 'stdout' or a path ending in {', '.join(_FILE_EXTENSIONS)} "
        f"(or starting with '.env')."
    )


__all__ = [
    "StorageBackend",
    "StdoutStorage",
    "DotEnvStorage",
    "JsonStorage",
    "TomlStorage",
    "YamlStorage",
    "get_storage",
]
