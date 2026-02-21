"""Tests for the JSON storage backend."""

import json
from pathlib import Path

from pyenvgen.storage import JsonStorage
from . import schema


class TestJsonStorage:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        s = schema("A", "B")
        JsonStorage(p).store({"A": "1", "B": "2"}, s)
        data = json.loads(p.read_text())
        assert data["A"] == "1"
        assert data["B"] == "2"

    def test_preserves_unrelated_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        p.write_text(json.dumps({"UNRELATED": "keep", "A": "old"}))
        s = schema("A")
        JsonStorage(p).store({"A": "new"}, s)
        data = json.loads(p.read_text())
        assert data["UNRELATED"] == "keep"
        assert data["A"] == "new"

    def test_internal_vars_excluded(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        s = schema("PUB", "PRIV", internal={"PRIV"})
        JsonStorage(p).store({"PUB": "x", "PRIV": "y"}, s)
        data = json.loads(p.read_text())
        assert "PUB" in data
        assert "PRIV" not in data

    def test_empty_existing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        p.write_text("")
        s = schema("X")
        JsonStorage(p).store({"X": "1"}, s)
        assert json.loads(p.read_text())["X"] == "1"


class TestJsonLoad:
    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        assert JsonStorage(tmp_path / "out.json").load() == {}

    def test_load_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        p.write_text("")
        assert JsonStorage(p).load() == {}

    def test_load_values_as_strings(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        p.write_text(json.dumps({"A": "hello", "B": 42}))
        result = JsonStorage(p).load()
        assert result == {"A": "hello", "B": "42"}

    def test_roundtrip_store_then_load(self, tmp_path: Path) -> None:
        p = tmp_path / "out.json"
        s = schema("X", "Y")
        JsonStorage(p).store({"X": "10", "Y": "20"}, s)
        assert JsonStorage(p).load() == {"X": "10", "Y": "20"}
