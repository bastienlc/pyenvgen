"""Tests for the storage factory function."""

from pathlib import Path

import pytest

from pyenvgen.storage import (
    DotEnvStorage,
    JsonStorage,
    StdoutStorage,
    TomlStorage,
    YamlStorage,
    get_storage,
)


class TestGetStorage:
    def test_stdout_backend(self) -> None:
        backend = get_storage("stdout")
        assert isinstance(backend, StdoutStorage)

    def test_dotenv_by_name(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / ".env"))
        assert isinstance(backend, DotEnvStorage)

    def test_dotenv_local(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / ".env.local"))
        assert isinstance(backend, DotEnvStorage)

    def test_json_extension(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / "out.json"))
        assert isinstance(backend, JsonStorage)

    def test_toml_extension(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / "out.toml"))
        assert isinstance(backend, TomlStorage)

    def test_yaml_extension(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / "out.yaml"))
        assert isinstance(backend, YamlStorage)

    def test_yml_extension(self, tmp_path: Path) -> None:
        backend = get_storage(str(tmp_path / "out.yml"))
        assert isinstance(backend, YamlStorage)

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot determine storage format"):
            get_storage("nonexistent.xyz")

    def test_unknown_name_raises(self) -> None:
        with pytest.raises(ValueError):
            get_storage("notaformat")
