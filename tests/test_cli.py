"""Tests for the CLI entry-point (cli.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from pyenvgen.cli import main, _parse_overrides


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

SIMPLE_SCHEMA = """\
variables:
  FOO:
    generation:
      rule: default
      value: "generated_foo"
  BAR:
    generation:
      rule: default
      value: "generated_bar"
"""

JINJA_SCHEMA = """\
variables:
  HOST:
    generation:
      rule: default
      value: "localhost"
  DSN:
    generation:
      rule: default
      value: "postgres://{{ HOST }}/db"
"""

INT_SCHEMA = """\
variables:
  PORT:
    type: int
    generation:
      rule: default
      value: "8080"
    validation:
      range:
        min: 1
        max: 65535
"""


def _write_schema(path: Path, content: str) -> None:
    path.write_text(content)


# ---------------------------------------------------------------------------
# _parse_overrides
# ---------------------------------------------------------------------------


class TestParseOverrides:
    def test_empty_list(self) -> None:
        assert _parse_overrides([]) == {}

    def test_none_returns_empty(self) -> None:
        assert _parse_overrides(None) == {}

    def test_single_override(self) -> None:
        assert _parse_overrides(["FOO=bar"]) == {"FOO": "bar"}

    def test_multiple_overrides(self) -> None:
        result = _parse_overrides(["FOO=1", "BAR=2"])
        assert result == {"FOO": "1", "BAR": "2"}

    def test_value_with_equals(self) -> None:
        # Values may themselves contain '='
        assert _parse_overrides(["URL=a=b=c"]) == {"URL": "a=b=c"}

    def test_missing_equals_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_overrides(["NOEQUALS"])


# ---------------------------------------------------------------------------
# Basic CLI behaviour
# ---------------------------------------------------------------------------


class TestMainBasic:
    def test_stdout_output(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        main([str(schema_path)])
        out = capsys.readouterr().out
        assert "FOO=generated_foo" in out
        assert "BAR=generated_bar" in out

    def test_missing_schema_file_exits(self) -> None:
        with pytest.raises(SystemExit):
            main(["/nonexistent/path/schema.yaml"])

    def test_non_mapping_yaml_exits(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "bad.yaml"
        schema_path.write_text("- not a mapping\n")
        with pytest.raises(SystemExit):
            main([str(schema_path)])

    def test_invalid_schema_structure_exits(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "bad.yaml"
        schema_path.write_text(
            "variables:\n  X:\n    generation:\n      rule: unknown_rule\n      value: x\n"
        )
        with pytest.raises(SystemExit):
            main([str(schema_path)])

    def test_override_replaces_generated_value(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        main([str(schema_path), "-o", "FOO=overridden"])
        out = capsys.readouterr().out
        assert "FOO=overridden" in out
        assert "BAR=generated_bar" in out

    def test_invalid_override_format_exits(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        with pytest.raises(SystemExit):
            main([str(schema_path), "-o", "NOEQUALS"])

    def test_validation_failure_exits(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, INT_SCHEMA)
        with pytest.raises(SystemExit):
            main([str(schema_path), "-o", "PORT=not_an_int"])

    def test_unknown_storage_exits(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        with pytest.raises((SystemExit, ValueError)):
            main([str(schema_path), "-s", "unknown.xyz"])


# ---------------------------------------------------------------------------
# Existing value preservation (no --force)
# ---------------------------------------------------------------------------


class TestExistingValuePreservation:
    def test_existing_json_values_preserved(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"FOO": "existing_foo"}))

        main([str(schema_path), "-s", str(out_path)])

        result = json.loads(out_path.read_text())
        assert result["FOO"] == "existing_foo"
        assert result["BAR"] == "generated_bar"

    def test_existing_yaml_values_preserved(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.yaml"
        out_path.write_text(yaml.dump({"FOO": "existing_foo"}))

        main([str(schema_path), "-s", str(out_path)])

        result = yaml.safe_load(out_path.read_text())
        assert result["FOO"] == "existing_foo"
        assert result["BAR"] == "generated_bar"

    def test_existing_dotenv_values_preserved(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / ".env"
        out_path.write_text("FOO=existing_foo\n")

        main([str(schema_path), "-s", str(out_path)])

        content = out_path.read_text()
        assert "FOO=existing_foo" in content
        assert "BAR=generated_bar" in content

    def test_stdout_does_not_preserve_existing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        # stdout has no storage so every run regenerates from schema defaults
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        main([str(schema_path)])
        out = capsys.readouterr().out
        assert "FOO=generated_foo" in out

    def test_cli_override_takes_precedence_over_existing(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"FOO": "stored_foo"}))

        main([str(schema_path), "-s", str(out_path), "-o", "FOO=cli_foo"])

        result = json.loads(out_path.read_text())
        assert result["FOO"] == "cli_foo"

    def test_existing_value_available_to_jinja_template(self, tmp_path: Path) -> None:
        """Existing HOST from storage is loaded *before* generation so that
        DSN's Jinja template can reference the stored HOST value."""
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, JINJA_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"HOST": "prod-db"}))

        main([str(schema_path), "-s", str(out_path)])

        result = json.loads(out_path.read_text())
        assert result["HOST"] == "prod-db"
        assert result["DSN"] == "postgres://prod-db/db"

    def test_no_existing_file_generates_from_schema(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.json"  # does not exist yet

        main([str(schema_path), "-s", str(out_path)])

        result = json.loads(out_path.read_text())
        assert result["FOO"] == "generated_foo"
        assert result["BAR"] == "generated_bar"


# ---------------------------------------------------------------------------
# --force flag
# ---------------------------------------------------------------------------


class TestForceFlag:
    def test_force_ignores_existing_values(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"FOO": "old_foo", "BAR": "old_bar"}))

        main([str(schema_path), "-s", str(out_path), "--force"])

        result = json.loads(out_path.read_text())
        assert result["FOO"] == "generated_foo"
        assert result["BAR"] == "generated_bar"

    def test_force_regenerates_from_schema_defaults(self, tmp_path: Path) -> None:
        """With --force the stored HOST is ignored, so DSN uses the schema default."""
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, JINJA_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"HOST": "prod-db"}))

        main([str(schema_path), "-s", str(out_path), "--force"])

        result = json.loads(out_path.read_text())
        assert result["HOST"] == "localhost"
        assert result["DSN"] == "postgres://localhost/db"

    def test_force_with_cli_override(self, tmp_path: Path) -> None:
        """--force ignores storage, but explicit -o overrides still apply."""
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, SIMPLE_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"FOO": "old"}))

        main([str(schema_path), "-s", str(out_path), "--force", "-o", "FOO=cli_val"])

        result = json.loads(out_path.read_text())
        assert result["FOO"] == "cli_val"
        assert result["BAR"] == "generated_bar"

    def test_without_force_existing_overrides_default_in_template(
        self, tmp_path: Path
    ) -> None:
        """Contrast with force: without --force the stored HOST seeds the Jinja
        context so DSN is built from the stored HOST, not the schema default."""
        schema_path = tmp_path / "schema.yaml"
        _write_schema(schema_path, JINJA_SCHEMA)
        out_path = tmp_path / "out.json"
        out_path.write_text(json.dumps({"HOST": "staging-db"}))

        main([str(schema_path), "-s", str(out_path)])

        result = json.loads(out_path.read_text())
        assert result["HOST"] == "staging-db"
        assert result["DSN"] == "postgres://staging-db/db"
