"""TOML storage backend – write environment variables to a TOML file."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from pyenvgen.schema import EnvSchema


class TomlStorage:
    """Write environment variables to a TOML file.

    The update is non-destructive: unrelated keys already present in the
    file are preserved.  Managed variables are written as strings at the
    top level (no table).
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def store(
        self,
        values: dict[str, Any],
        schema: EnvSchema,
    ) -> None:
        from pyenvgen.storage import _public_values

        public = _public_values(values, schema)

        existing: dict[str, Any] = {}
        if self.path.exists():
            text = self.path.read_text().strip()
            if text:
                existing = tomllib.loads(text)

        existing.update(public)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(tomli_w.dumps(existing).encode())
