"""JSON storage backend – write environment variables to a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyenvgen.schema import EnvSchema


class JsonStorage:
    """Write environment variables to a JSON file.

    The update is non-destructive: unrelated keys already present in the
    file are preserved.  Managed variables are set or updated at the
    top level of the JSON object.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, str]:
        """Return existing key-value pairs from the JSON file."""
        if not self.path.exists():
            return {}
        text = self.path.read_text().strip()
        if not text:
            return {}
        data = json.loads(text)
        if not isinstance(data, dict):
            return {}
        return {k: str(v) for k, v in data.items()}

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
                existing = json.loads(text)

        existing.update(public)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(existing, indent=2) + "\n")
