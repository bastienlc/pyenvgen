"""Tests for the TOML storage backend."""

import tomllib
from pathlib import Path

import tomli_w

from pyenvgen.storage import TomlStorage
from . import schema


class TestTomlStorage:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("A", "B")
        TomlStorage(p).store({"A": "1", "B": "2"}, s)
        data = tomllib.loads(p.read_text())
        assert data["A"] == "1"
        assert data["B"] == "2"

    def test_preserves_unrelated_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        p.write_bytes(tomli_w.dumps({"UNRELATED": "keep", "A": "old"}).encode())
        s = schema("A")
        TomlStorage(p).store({"A": "new"}, s)
        data = tomllib.loads(p.read_text())
        assert data["UNRELATED"] == "keep"
        assert data["A"] == "new"

    def test_internal_vars_excluded(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("PUB", "PRIV", internal={"PRIV"})
        TomlStorage(p).store({"PUB": "x", "PRIV": "y"}, s)
        data = tomllib.loads(p.read_text())
        assert "PUB" in data
        assert "PRIV" not in data


class TestTomlLoad:
    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        assert TomlStorage(tmp_path / "out.toml").load() == {}

    def test_load_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        p.write_text("")
        assert TomlStorage(p).load() == {}

    def test_load_values_as_strings(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        p.write_bytes(tomli_w.dumps({"A": "hello", "B": "42"}).encode())
        result = TomlStorage(p).load()
        assert result == {"A": "hello", "B": "42"}

    def test_roundtrip_store_then_load(self, tmp_path: Path) -> None:
        p = tmp_path / "out.toml"
        s = schema("X", "Y")
        TomlStorage(p).store({"X": "10", "Y": "20"}, s)
        assert TomlStorage(p).load() == {"X": "10", "Y": "20"}
