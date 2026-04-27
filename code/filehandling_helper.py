"""
Helper functions for file handling operations.
"""
import re
from pathlib import Path
from shutil import move, copy2
from typing import Callable, Any

def _process_files_by_regex(source: Path, destination: Path, regex_pattern: str,
                             file_operation: Callable[..., Any],
                             print_progress: bool = False) -> None:
    """Internal helper that applies a file operation to all files matching a regex.

    Not intended to be called directly — use move_files_by_regex or
    copy_files_by_regex instead."""

    destination.mkdir(parents=True, exist_ok=True)
    try:
        compiled_regex = re.compile(regex_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"❌ Invalid regex pattern '{regex_pattern}': {e}")
        return
    for file_path in [f for f in source.iterdir() if f.is_file()]:
        if compiled_regex.search(file_path.name):
            dest_file = destination / file_path.name
            file_operation(str(file_path), str(dest_file))
            if print_progress:
                print(f"{file_operation.__name__}: {file_path} -> {dest_file}")

def move_files_by_regex(source: Path, destination: Path, regex_pattern: str,
                        print_progress: bool = False) -> None:
    """Move all files matching regex from source to destination. Deletes originals."""
    _process_files_by_regex(source, destination, regex_pattern, move, print_progress)

def copy_files_by_regex(source: Path, destination: Path, regex_pattern: str,
                        print_progress: bool = False) -> None:
    """Copy all files matching regex from source to destination. Keeps originals."""
    _process_files_by_regex(source, destination, regex_pattern, copy2, print_progress)
