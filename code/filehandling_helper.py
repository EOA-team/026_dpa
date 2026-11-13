"""
Helper functions for file handling operations.
"""

import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from shutil import copy2, move
from typing import Any


def _process_files_by_regex(
    source: Path,
    destination: Path,
    regex_pattern: str,
    file_operation: Callable[..., Any],
    print_progress: bool = False,
) -> None:
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


def move_files_by_regex(
    source: Path, destination: Path, regex_pattern: str, print_progress: bool = False
) -> None:
    """Move all files matching regex from source to destination. Deletes originals."""
    _process_files_by_regex(source, destination, regex_pattern, move, print_progress)


def copy_files_by_regex(
    source: Path, destination: Path, regex_pattern: str, print_progress: bool = False
) -> None:
    """Copy all files matching regex from source to destination. Keeps originals."""
    _process_files_by_regex(source, destination, regex_pattern, copy2, print_progress)


def parse_t04_datetime(filename: str) -> datetime:
    """Extract the datetime encoded in a T04 filename (naive, same timezone as log).

    T04 filenames end with YYYYMMDDHHMM before the extension, e.g.:
        6234C84164202605260836.T04 -> 2026-05-26 08:36
    """
    name_part = filename.split(".", maxsplit=1)[0]
    return datetime.strptime(name_part[-12:], "%Y%m%d%H%M")


def get_flight_log_time_range(log_file: Path) -> tuple[datetime, datetime]:
    """Derive the overall acquisition time range from a flight log file.

    Scans every line for datetimes in the format YYYY-MM-DDTHHMMSS
    (e.g. 2026-05-26T085926) and returns (min, max) of all found values.
    Robust to header lines and column layout.
    """
    datetime_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{6}")
    datetimes = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            for match in datetime_pattern.findall(line):
                datetimes.append(datetime.strptime(match, "%Y-%m-%dT%H%M%S"))
    if not datetimes:
        raise ValueError(f"No flight timestamps found in log file: {log_file}")
    return min(datetimes), max(datetimes)
