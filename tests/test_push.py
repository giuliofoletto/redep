import pytest

from redep.push import push
from redep.util import read_config_file

from pathlib import Path


def clean():
    dst_dir = Path(__file__).parent / "dst_dir"
    if dst_dir.exists():
        for item in dst_dir.glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                for subitem in item.glob("**/*"):
                    if subitem.is_file():
                        subitem.unlink()
                item.rmdir()
        dst_dir.rmdir()


def test_read_config_file():
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, destinations = read_config_file(config_path)
    assert root_dir == config_path.parent
    assert matches == [Path("**/*")]
    assert ignores == [Path("./redep.toml"), Path("./to_ignore.txt")]
    assert destinations == [
        {
            "host": "",
            "path": (root_dir / "../dst_dir").resolve(),
        }
    ]


def test_push_local():
    clean()
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, destinations = read_config_file(config_path)
    push(root_dir, matches, ignores, destinations)
    dst_dir = Path(__file__).parent / "dst_dir"
    assert dst_dir.exists()
    expected_files = [
        dst_dir / "to_push.txt",
    ]
    for file in expected_files:
        assert file.exists()
    ignored_files = [
        dst_dir / "redep.toml",
        dst_dir / "to_ignore.txt",
    ]
    for file in ignored_files:
        assert not file.exists()
    clean()
