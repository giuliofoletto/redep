import glob
import shutil
from pathlib import Path

import pytest

from redep.pull import pull, pull_local
from redep.util import read_config_file, select_patterns


def clean():
    dst_dir = Path(__file__).parent / "pulled_dir"
    shutil.rmtree(dst_dir, ignore_errors=True)


def prepare():
    dst_dir = Path(__file__).parent / "pulled_dir"
    if not dst_dir.exists():
        dst_dir.mkdir()
    config = dst_dir / "redep.toml"
    with open(config, "w") as f:
        f.write(
            """
    # redep configuration file
root_dir = "./"  # In most cases, keep as is. This means the root directory is the directory where this config file is located.

match = ["**/*"]  # In most cases, keep as is. This means all files in the root directory and subdirectories are considered for deployment.

ignore = ["./redep.toml", "./to_ignore.txt", "./to_ignore/**"]
    
[[remotes]]
host = ""  # Replace with remote host or leave empty for local push
path = "../src_dir"  # Replace with path on the host. For local push, this is relative to the directory of the config file.
    """
        )
    return


def test_pull_local():
    prepare()
    config_path = Path(__file__).parent / "pulled_dir" / "redep.toml"
    root_dir, matches, ignores, sources = read_config_file(config_path)
    pull_from = Path(sources[0]["path"])
    if not pull_from.is_absolute():
        pull_from = (Path(root_dir) / sources[0]["path"]).resolve()
    selected_files, selected_dirs, ignored_files, ignored_dirs = select_patterns(
        pull_from, matches, ignores
    )
    pull_local(selected_files, selected_dirs, pull_from, root_dir)
    dst_dir = Path(__file__).parent / "pulled_dir"
    expected_files = {
        dst_dir
        / "redep.toml",  # This is ignored, but it is already there from preparation
        dst_dir / "to_push.txt",
        dst_dir / "to_push" / "to_push.txt",
    }
    for file in expected_files:
        assert file.exists()
    ignored_files = {
        dst_dir / "to_ignore.txt",
        dst_dir / "to_ignore" / "to_ignore.txt",
    }
    for file in ignored_files:
        assert not file.exists()
    existing_files = glob.glob(str(dst_dir / "**" / "*"), recursive=True)
    existing_files = {Path(f) for f in existing_files if Path(f).is_file()}
    assert existing_files == expected_files
    clean()


def test_pull_with_local_source():
    """
    Test the full pull function with a local source.
    """
    prepare()
    config_path = Path(__file__).parent / "pulled_dir" / "redep.toml"
    root_dir, matches, ignores, sources = read_config_file(config_path)
    pull_from = Path(sources[0]["path"])
    if not pull_from.is_absolute():
        pull_from = (Path(root_dir) / sources[0]["path"]).resolve()
    pull(root_dir, matches, ignores, sources)
    dst_dir = Path(__file__).parent / "pulled_dir"
    expected_files = {
        dst_dir
        / "redep.toml",  # This is ignored, but it is already there from preparation
        dst_dir / "to_push.txt",
        dst_dir / "to_push" / "to_push.txt",
    }
    for file in expected_files:
        assert file.exists()
    ignored_files = {
        dst_dir / "to_ignore.txt",
        dst_dir / "to_ignore" / "to_ignore.txt",
    }
    for file in ignored_files:
        assert not file.exists()
    existing_files = glob.glob(str(dst_dir / "**" / "*"), recursive=True)
    existing_files = {Path(f) for f in existing_files if Path(f).is_file()}
    assert existing_files == expected_files
    clean()
