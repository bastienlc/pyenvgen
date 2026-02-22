"""Komodo storage backend – write environment variables to a Komodo TOML file."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from pyenvgen.schema import EnvSchema


class KomodoStorage:
    """Write environment variables to a Komodo TOML file.

    The update is non-destructive: unrelated content already present in the
    file is preserved.  Managed variables are written as an array of tables
    using the [[variable]] syntax, where each entry has 'name' and 'value'
    fields.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, str]:
        """Return existing key-value pairs from the Komodo TOML file."""
        if not self.path.exists():
            return {}
        text = self.path.read_text().strip()
        if not text:
            return {}
        data = tomllib.loads(text)
        variables = data.get("variable", [])
        return {entry["name"]: str(entry["value"]) for entry in variables}

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

        # Convert the public values dict to the komodo format
        variables = [{"name": k, "value": str(v)} for k, v in public.items()]

        # Update the existing data with the new variables array
        existing["variable"] = variables

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(tomli_w.dumps(existing).encode())
