"""CLI entry-point for pyenvgen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from marshmallow import ValidationError as MarshmallowValidationError
from pydantic import ValidationError

from pyenvgen.generation import generate_env
from pyenvgen.schema import EnvSchema
from pyenvgen.storage import get_storage
from pyenvgen.validation import validate_env


def _load_schema(path: Path) -> EnvSchema:
    """Load and validate a YAML schema file."""
    try:
        with open(path) as f:
            raw: Any = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: schema file not found: {path}")
        sys.exit(1)

    if not isinstance(raw, dict):
        print(f"Error: schema file must be a YAML mapping, got {type(raw).__name__}")
        sys.exit(1)

    try:
        return EnvSchema.model_validate(raw)
    except ValidationError as exc:
        print(f"Schema validation error:\n{exc}")
        sys.exit(1)


def _parse_overrides(override_args: list[str] | None) -> dict[str, str]:
    """Parse ``KEY=VALUE`` override arguments from the CLI."""
    overrides: dict[str, str] = {}
    for item in override_args or []:
        if "=" not in item:
            print(f"Error: override must be KEY=VALUE, got '{item}'")
            sys.exit(1)
        key, value = item.split("=", 1)
        overrides[key] = value
    return overrides


def main(argv: list[str] | None = None) -> None:
    """Main entry-point."""
    parser = argparse.ArgumentParser(
        prog="pyenvgen",
        description="Generate environment variables from a YAML schema.",
    )
    parser.add_argument(
        "schema",
        type=Path,
        help="Path to the YAML schema file.",
    )
    parser.add_argument(
        "-s",
        "--storage",
        default="stdout",
        help="Storage backend (default: stdout).",
    )
    parser.add_argument(
        "-b",
        "--backend",
        choices=["dotenv", "json", "toml", "yaml", "komodo"],
        help="Explicitly specify the storage backend type (useful for ambiguous file extensions).",
    )
    parser.add_argument(
        "-o",
        "--override",
        action="append",
        metavar="KEY=VALUE",
        help="Override a generated value (can be repeated).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Regenerate all values, ignoring any values already present in "
            "the storage backend. Without this flag, existing values are "
            "preserved and used as the base before new ones are generated."
        ),
    )

    args = parser.parse_args(argv)

    # 1. Load & validate schema
    schema = _load_schema(args.schema)

    # 2. Get storage backend early so we can load existing values
    backend = get_storage(args.storage, args.backend)

    # 3. Parse CLI overrides
    overrides = _parse_overrides(args.override)

    # 4. Load existing values from storage and merge with CLI overrides.
    #    This happens *before* generation so that existing values are available
    #    to Jinja templates inside generation rules.  CLI overrides always take
    #    precedence over stored values; --force skips loading altogether.
    if args.force:
        merged: dict[str, str] = overrides
    else:
        existing = backend.load()
        merged = {**existing, **overrides}

    # 5. Generate values (existing / overridden values seed the result dict)
    generated = generate_env(schema, overrides=merged)

    # 6. Validate generated values against schema (type-cast + constraints)
    try:
        validated = validate_env(schema, generated)
    except MarshmallowValidationError as exc:
        print(f"Validation error: {exc}")
        sys.exit(1)

    # 7. Store output
    backend.store(validated, schema)
