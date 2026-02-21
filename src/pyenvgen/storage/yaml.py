"""YAML storage backend – write environment variables to a YAML file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pyenvgen.schema import EnvSchema


class YamlStorage:
    """Write environment variables to a YAML file.

    The update is non-destructive: unrelated keys already present in the
    file are preserved.  Managed variables are written as strings at the
    top level.
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
                loaded = yaml.safe_load(text)
                if isinstance(loaded, dict):
                    existing = loaded

        existing.update(public)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.dump(existing, default_flow_style=False, allow_unicode=True)
        )
