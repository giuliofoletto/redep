from pathlib import Path

import pytest

from redep.util import (read_config_file, select_leaf_directories,
                        select_patterns)


def test_read_config_file():
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, remotes = read_config_file(config_path)
    assert root_dir == config_path.parent
    assert matches == [Path("*"), Path("**/*")]
    assert ignores == [
        Path("./redep.toml"),
        Path("./to_ignore.txt"),
        Path("./to_ignore/**"),
    ]
    assert remotes == [
        {
            "host": "",
            "path": (root_dir / "../dst_dir").resolve(),
        }
    ]


def test_select_patterns():
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, remotes = read_config_file(config_path)
    selected_files, selected_dirs, ignored_files, ignored_dirs = select_patterns(
        root_dir, matches, ignores
    )
    expected_selected_files = {
        root_dir / "to_push.txt",
        root_dir / "to_push" / "to_push.txt",
    }
    expected_selected_dirs = {
        root_dir,
        root_dir / "to_push",
    }
    expected_ignored_files = {
        root_dir / "redep.toml",
        root_dir / "to_ignore.txt",
        root_dir / "to_ignore" / "to_ignore.txt",
    }
    expected_ignored_dirs = {
        root_dir / "to_ignore",
    }
    assert selected_files == expected_selected_files
    assert selected_dirs == expected_selected_dirs
    assert ignored_files == expected_ignored_files
    assert ignored_dirs == expected_ignored_dirs
    for f in selected_files:
        assert f.parent in selected_dirs


def test_select_leaf_directories():
    dirs = {
        Path("a"),
        Path("a/b"),
        Path("a/b/c"),
        Path("a/b/c/d"),
        Path("a/b/d"),
        Path("a/e"),
        Path("f"),
    }
    expected_leaf_dirs = {
        Path("a/b/c/d"),
        Path("a/b/d"),
        Path("a/e"),
        Path("f"),
    }
    assert select_leaf_directories(dirs) == expected_leaf_dirs
