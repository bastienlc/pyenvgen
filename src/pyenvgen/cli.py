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
    with open(path) as f:
        raw: Any = yaml.safe_load(f)

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
        "-o",
        "--override",
        action="append",
        metavar="KEY=VALUE",
        help="Override a generated value (can be repeated).",
    )

    args = parser.parse_args(argv)

    # 1. Load & validate schema
    schema = _load_schema(args.schema)

    # 2. Parse overrides
    overrides = _parse_overrides(args.override)

    # 3. Generate values
    generated = generate_env(schema, overrides=overrides)

    # 4. Validate generated values against schema (type-cast + constraints)
    try:
        validated = validate_env(schema, generated)
    except MarshmallowValidationError as exc:
        print(f"Validation error: {exc}")
        sys.exit(1)

    # 5. Store output
    backend = get_storage(args.storage)
    backend.store(validated, schema)
