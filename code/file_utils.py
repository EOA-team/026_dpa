""" Basic utility functions for file handling and  path management"""

import logging
from shutil import copy2
import sys
import zipfile
from datetime import datetime
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def check_path_exists(path: str | Path, message: str = "") -> None:
    """Check if path exists.
    Allows for an optional message to provide additional context in the error.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {path}\n{message}" if message else
            f"Path does not exist: {path}"
        )


def get_base_path(caller_file: str | Path) -> Path:
    """Get base path - works for both script and PyInstaller executable.
    caller_file : str | Path
        Pass __file__ from the calling script.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(caller_file).parent


def check_drive_mounted(path: str | Path) -> None:
    """Check if the drive or mount point for the given path is mounted.

    Raises:
        FileNotFoundError: If the drive/mount point is not mounted.
    """
    path = Path(path)
    mount_point = Path(path.anchor)  # e.g. 'Q:\\'

    if not mount_point.exists():
        raise FileNotFoundError(
            f"Drive or mount point not accessible: {mount_point}\n"
            "Check that the drive is mounted or network share is connected."
        )


def copy_with_logging(src, dst):
    """Copy function with size info."""
    size = Path(src).stat().st_size / (1024 * 1024)  # MB
    logger.info("Copying %s (%.2f MB)", Path(src).name, size)
    return copy2(src, dst,)


def wait_for_folder_stable(folder: Path, timeout: int,
                           stable_seconds: int, debug: bool) -> None:
    """Wait until no files in folder are modified for stable_seconds consecutive seconds."""
    start = time.time()
    last_mtime = 0.0
    stable_count = 0
    last_printed_file: Path | None = None

    while stable_count < stable_seconds:
        if time.time() - start > timeout:
            raise TimeoutError(
                f"Folder did not stabilize within {timeout}s: {folder}")

        files = [f for f in folder.rglob("*") if f.is_file()]
        current_mtime = max((f.stat().st_mtime for f in files), default=0.0)
        newest_file = max(files, key=lambda f: f.stat().st_mtime, default=None)

        if debug and newest_file and newest_file != last_printed_file:
            timestamp = datetime.fromtimestamp(
                current_mtime).strftime('%H:%M:%S.%f')[:-3]
            print(f"Newest: {newest_file.name} - {timestamp}")
            last_printed_file = newest_file

        stable_count = stable_count + 1 if current_mtime == last_mtime else 0
        last_mtime = current_mtime
        time.sleep(1)

    print(f"Folder stable: {folder}")


def wait_for_file_creation(
        file_path:    Path,
        timeout_s: int
) -> None:
    """Wait until a specific file is created.

    Args:
        file:    Path to the file to wait for.
        timeout: Maximum time to wait in seconds before raising TimeoutError.
    """
    start = time.time()

    while not file_path.exists():
        if time.time() - start > timeout_s:
            raise TimeoutError(
                f"File was not created within {timeout_s}s: {file_path}")
        time.sleep(2)

    print(f"File created: {file_path}")


def wait_for_file_count(
        folder:         Path,
        expected_count: int,
        pattern:        str = "*.*",
        timeout_s:      int = 300,
) -> None:
    """Wait until a folder contains at least `expected_count` files matching `pattern`.

    Example usage:
    wait_for_file_count(
        folder=Path("/path/to/folder"),
        expected_count=6,
        pattern="*.txt",
        timeout_s=10
    )
    """
    start = time.time()

    while len(list(folder.glob(pattern))) < expected_count:
        if time.time() - start > timeout_s:
            raise TimeoutError(
                f"Expected {expected_count} file(s) matching '{pattern}' "
                f"not found within {timeout_s}s: {folder}"
                )
        time.sleep(2)

    print(f"Found {expected_count} file(s) matching '{pattern}' in {folder}")


def move_and_extract_downloaded_zip(output_folder: Path) -> None:
    """Find the newest zip file in downloads, extract it to output folder and delete the zip."""
    download_folder = Path.home() / "Downloads"

    zip_files = list(download_folder.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No zip files found in {download_folder}")

    newest_zip = max(zip_files, key=lambda f: f.stat().st_mtime)

    output_folder.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(newest_zip, 'r') as zip_ref:
        zip_ref.extractall(output_folder)

    newest_zip.unlink()
    print(f"Extracted {newest_zip.name} to {output_folder} and deleted zip.")


def find_las_file(folder: Path):
    """Find the single .las file in the given directory. Raises error if not exactly one found."""
    files = list(folder.rglob("*.las"))
    if len(files) == 0:
        raise FileNotFoundError(f"No .las file found in {folder}")
    if len(files) > 1:
        raise ValueError(f"Expected exactly one .las file, but found {len(files)}:\n" +
                         "\n".join(str(f) for f in files))
    return files[0]
