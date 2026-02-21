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
