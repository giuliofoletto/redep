import pytest
import glob

from redep.push import push, push_local
from redep.util import read_config_file, select_patterns

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


def test_push_local():
    clean()
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, destinations = read_config_file(config_path)
    selected_files, selected_dirs, _, _ = select_patterns(root_dir, matches, ignores)
    push_local(selected_files, selected_dirs, root_dir, destinations[0]["path"])
    dst_dir = Path(__file__).parent / "dst_dir"
    assert dst_dir.exists()
    expected_files = {
        dst_dir / "to_push.txt",
        dst_dir / "to_push" / "to_push.txt",
    }
    for file in expected_files:
        assert file.exists()
    ignored_files = {
        dst_dir / "redep.toml",
        dst_dir / "to_ignore.txt",
        dst_dir / "to_ignore" / "to_ignore.txt",
    }
    for file in ignored_files:
        assert not file.exists()
    existing_files = glob.glob(str(dst_dir / "**" / "*"), recursive=True)
    existing_files = {Path(f) for f in existing_files if Path(f).is_file()}
    assert existing_files == expected_files
    clean()


def test_push_with_local_destination():
    """
    Test the full push function with a local destination.
    """
    clean()
    config_path = Path(__file__).parent / "src_dir" / "redep.toml"
    root_dir, matches, ignores, destinations = read_config_file(config_path)
    push(root_dir, matches, ignores, destinations)
    dst_dir = Path(__file__).parent / "dst_dir"
    assert dst_dir.exists()
    expected_files = {
        dst_dir / "to_push.txt",
        dst_dir / "to_push" / "to_push.txt",
    }
    for file in expected_files:
        assert file.exists()
    ignored_files = {
        dst_dir / "redep.toml",
        dst_dir / "to_ignore.txt",
        dst_dir / "to_ignore" / "to_ignore.txt",
    }
    for file in ignored_files:
        assert not file.exists()
    existing_files = glob.glob(str(dst_dir / "**" / "*"), recursive=True)
    existing_files = {Path(f) for f in existing_files if Path(f).is_file()}
    assert existing_files == expected_files
    clean()
