"""
Helper functions for file handling operations.
"""
import re
from pathlib import Path
from shutil import move


def move_files_by_regex(source: Path, destination: Path, regex_pattern: str,
                        print_progress: bool = False) -> None:
    """
    Move all files where filename matches the regex pattern (case-insensitive).
    Examples: 
                        - r"vnir" - matches files containing 'vnir'
                        - r"^v1240" - matches files starting with 'v1240'
                        - r"\.(hdr|hyspex)$" - matches .hdr or .hyspex files
    """

    # Create destination directory if it doesn't exist
    destination.mkdir(parents=True, exist_ok=True)

    # Compile regex pattern (case-insensitive)
    try:
        compiled_regex = re.compile(regex_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"❌ Invalid regex pattern '{regex_pattern}': {e}")

    # Get all files in source directory
    all_files = [f for f in source.iterdir() if f.is_file()]

    for file_path in all_files:
        # Check if pattern matches filename
        if compiled_regex.search(file_path.name):
            dest_file = destination / file_path.name
            move(str(file_path), str(dest_file))
            if print_progress:
                print(f"Moved: {file_path} -> {dest_file}")
