""" Basic utility functions for file handling and  path management"""

import logging
from shutil import copy2
import sys
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
