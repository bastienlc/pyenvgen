"""Tests for the Komodo storage backend."""

import tomllib
from pathlib import Path

import tomli_w

from pyenvgen.storage import KomodoStorage
from . import schema


class TestKomodoStorage:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("A", "B")
        KomodoStorage(p).store({"A": "1", "B": "2"}, s)
        data = tomllib.loads(p.read_text())
        assert "variable" in data
        variables = data["variable"]
        assert len(variables) == 2
        assert {"name": "A", "value": "1"} in variables
        assert {"name": "B", "value": "2"} in variables

    def test_preserves_unrelated_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        # Create initial file with unrelated content and existing variables
        initial_data = {
            "unrelated": "keep",
            "nested": {"key": "value"},
            "variable": [
                {"name": "A", "value": "old"},
                {"name": "OLD_VAR", "value": "old_value"},
            ],
        }
        p.write_bytes(tomli_w.dumps(initial_data).encode())

        s = schema("A")
        KomodoStorage(p).store({"A": "new"}, s)

        data = tomllib.loads(p.read_text())
        assert data["unrelated"] == "keep"
        assert data["nested"] == {"key": "value"}
        # Only A should be in variables now (OLD_VAR is removed since it's not in schema)
        variables = data["variable"]
        assert len(variables) == 1
        assert {"name": "A", "value": "new"} in variables

    def test_internal_vars_excluded(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("PUB", "PRIV", internal={"PRIV"})
        KomodoStorage(p).store({"PUB": "x", "PRIV": "y"}, s)
        data = tomllib.loads(p.read_text())
        variables = data["variable"]
        names = {v["name"] for v in variables}
        assert "PUB" in names
        assert "PRIV" not in names


class TestKomodoLoad:
    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        assert KomodoStorage(tmp_path / "out.toml").load() == {}

    def test_load_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        p.write_text("")
        assert KomodoStorage(p).load() == {}

    def test_load_values_as_strings(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        data = {
            "variable": [
                {"name": "A", "value": "hello"},
                {"name": "B", "value": "42"},
            ]
        }
        p.write_bytes(tomli_w.dumps(data).encode())
        result = KomodoStorage(p).load()
        assert result == {"A": "hello", "B": "42"}

    def test_roundtrip_store_then_load(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("X", "Y")
        KomodoStorage(p).store({"X": "10", "Y": "20"}, s)
        assert KomodoStorage(p).load() == {"X": "10", "Y": "20"}

    def test_load_file_without_variables(self, tmp_path: Path) -> None:
        """Test loading a file that has other content but no [[variable]] section."""
        p = tmp_path / "out.toml"
        data = {"other": "content", "nested": {"key": "value"}}
        p.write_bytes(tomli_w.dumps(data).encode())
        result = KomodoStorage(p).load()
        assert result == {}
