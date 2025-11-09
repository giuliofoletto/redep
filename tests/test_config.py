import pytest

import tomllib
from pathlib import Path

from redep.config import (
    init,
    add_remote,
    remove_remote,
    add_ignore_pattern,
    remove_ignore_pattern,
)


def clean():
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    if config_path.exists():
        config_path.unlink()
    if config_dir_path.exists():
        config_dir_path.rmdir()


def test_init():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)
    assert config_path.exists()
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert config_data["root_dir"] == "./"
    assert config_data["match"] == ["*", "**/*"]
    assert config_data["ignore"] == [f"./{str(config_path.name).replace('\\', '/')}"]
    assert config_data["remotes"] == []
    clean()


def test_init_with_config():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    custom_config = {
        "root_dir": "./custom_root",
        "match": ["**/*.py"],
        "ignore": ["./ignore_this.txt"],
        "remotes": [{"host": "example.com", "path": "/remote/path"}],
    }
    init(config_path, custom_config)
    assert config_path.exists()
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert config_data == custom_config
    clean()


def test_init_existing_file():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)
    # Try initializing again, with a difference; should raise logging.error but not overwrite
    custom_config = {
        "root_dir": "./custom_root",
        "match": ["**/*.py"],
        "ignore": ["./ignore_this.txt"],
        "remotes": [{"host": "example.com", "path": "/remote/path"}],
    }
    init(config_path, custom_config)
    assert config_path.exists()
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert config_data["root_dir"] == "./"  # default, not taken from custom_config
    clean()


def test_add_remote():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)

    add_remote(config_path, "user@host:/remote/path")
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert config_data["remotes"] == [{"host": "user@host", "path": "/remote/path"}]
    clean()


def test_remove_remote():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)

    add_remote(config_path, "user@host:/remote/path")
    remove_remote(config_path, "user@host:/remote/path")
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert config_data["remotes"] == []
    clean()


def test_add_ignore_pattern():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)

    add_ignore_pattern(config_path, "./*.txt")
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert "./*.txt" in config_data["ignore"]
    clean()


def test_remove_ignore_pattern():
    clean()
    config_dir_path = Path(__file__).parent / "temp"
    config_path = config_dir_path / "redep.toml"
    config_dir_path.mkdir(exist_ok=True)
    init(config_path)

    add_ignore_pattern(config_path, "./*.txt")
    remove_ignore_pattern(config_path, "./*.txt")
    with open(config_path, "rb") as config_file:
        config_data = tomllib.load(config_file)
    assert "./*.txt" not in config_data["ignore"]
    clean()
