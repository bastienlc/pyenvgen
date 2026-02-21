"""Tests for the YAML storage backend."""

from pathlib import Path

import yaml

from pyenvgen.storage import YamlStorage
from . import schema


class TestYamlStorage:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.yaml"
        s = schema("A", "B")
        YamlStorage(p).store({"A": "1", "B": "2"}, s)
        data = yaml.safe_load(p.read_text())
        assert data["A"] == "1"
        assert data["B"] == "2"

    def test_preserves_unrelated_keys(self, tmp_path: Path) -> None:
        p = tmp_path / "out.yaml"
        p.write_text(yaml.dump({"UNRELATED": "keep", "A": "old"}))
        s = schema("A")
        YamlStorage(p).store({"A": "new"}, s)
        data = yaml.safe_load(p.read_text())
        assert data["UNRELATED"] == "keep"
        assert data["A"] == "new"

    def test_internal_vars_excluded(self, tmp_path: Path) -> None:
        p = tmp_path / "out.yaml"
        s = schema("PUB", "PRIV", internal={"PRIV"})
        YamlStorage(p).store({"PUB": "x", "PRIV": "y"}, s)
        data = yaml.safe_load(p.read_text())
        assert "PUB" in data
        assert "PRIV" not in data

    def test_yml_extension(self, tmp_path: Path) -> None:
        p = tmp_path / "out.yml"
        s = schema("X")
        YamlStorage(p).store({"X": "42"}, s)
        assert yaml.safe_load(p.read_text())["X"] == "42"
