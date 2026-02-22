"""Komodo storage backend – write environment variables to a Komodo TOML file."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from pyenvgen.schema import EnvSchema

# Characters that must be escaped inside a TOML basic string.
_TOML_ESCAPES = str.maketrans(
    {
        "\\": "\\\\",
        '"': '\\"',
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }
)


def _toml_str(s: str) -> str:
    """Return *s* as a quoted TOML basic string."""
    return '"' + s.translate(_TOML_ESCAPES) + '"'


def _variable_entry(name: str, value: str) -> str:
    """Render one [[variable]] array-of-tables entry."""
    return f"[[variable]]\nname = {_toml_str(name)}\nvalue = {_toml_str(value)}"


def _strip_variable_sections(text: str) -> str:
    """Remove all *variable* definitions from raw TOML text.

    Handles both the array-of-tables form (``[[variable]]``) and the inline
    form (``variable = [...]``) so that files written by older versions of
    pyenvgen are also handled correctly.  All other content is left verbatim.
    """
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    # State: "none" | "array_of_tables" | "inline_array"
    mode = "none"
    bracket_depth = 0

    for line in lines:
        stripped = line.strip()

        if mode == "none":
            if stripped.startswith("[[") and re.match(
                r"^\[\[\s*variable\s*\]\]", stripped
            ):
                mode = "array_of_tables"
                # Don't append – skip this line.
            elif re.match(r"^variable\s*=", stripped):
                mode = "inline_array"
                bracket_depth = stripped.count("[") - stripped.count("]")
                if bracket_depth <= 0:
                    mode = "none"
                # Don't append – skip this line.
            else:
                result.append(line)

        elif mode == "array_of_tables":
            # Stay in this mode until we hit a different TOML header.
            if stripped.startswith("[["):
                if re.match(r"^\[\[\s*variable\s*\]\]", stripped):
                    # Another [[variable]] entry – still in array_of_tables mode.
                    pass
                else:
                    mode = "none"
                    result.append(line)
            elif stripped.startswith("["):
                mode = "none"
                result.append(line)
            # Otherwise skip lines that belong to the current [[variable]] entry.

        elif mode == "inline_array":
            bracket_depth += stripped.count("[") - stripped.count("]")
            if bracket_depth <= 0:
                mode = "none"
            # Skip continuation lines of the inline array.

    return "".join(result)


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

        # Read the existing raw text so we can preserve its exact formatting.
        existing_text = ""
        if self.path.exists():
            existing_text = self.path.read_text()

        # Strip only the [[variable]] sections; everything else is kept verbatim.
        base_text = _strip_variable_sections(existing_text).rstrip()

        # Serialize each variable as its own [[variable]] entry.
        new_entries = [_variable_entry(k, str(v)) for k, v in public.items()]

        parts = ([base_text] if base_text else []) + new_entries
        result = "\n\n".join(parts) + "\n"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(result)
