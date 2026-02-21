"""Dotenv storage backend – write environment variables to a .env file."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pyenvgen.schema import EnvSchema


# Matches   KEY=value   or   export KEY=value   (with optional surrounding spaces)
_DOTENV_LINE_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


class DotEnvStorage:
    """Write environment variables to a .env file.

    The update is non-destructive: existing comments, blank lines and
    variables *not* managed by pyenvgen are left exactly as-is.  Managed
    variables that already appear in the file have their values updated in
    place; new variables are appended at the end.
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

        # Read existing lines (or start fresh).
        if self.path.exists():
            lines = self.path.read_text().splitlines(keepends=True)
        else:
            lines = []

        # Track which managed keys have been handled (updated in-place).
        handled: set[str] = set()
        new_lines: list[str] = []

        for line in lines:
            m = _DOTENV_LINE_RE.match(line)
            if m:
                key = m.group(1)
                if key in public:
                    # Replace this line with the new value.
                    # Preserve the `export ` prefix if it was there.
                    prefix = "export " if line.lstrip().startswith("export ") else ""
                    new_lines.append(f"{prefix}{key}={public[key]}\n")
                    handled.add(key)
                    continue
            new_lines.append(line)

        # Append any managed keys that were not already in the file.
        for key, value in public.items():
            if key not in handled:
                new_lines.append(f"{key}={value}\n")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(new_lines))
