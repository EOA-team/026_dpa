""" Basic helper functions for PostFlightDTT tool, 
which are being used in both drone_to_hd and hd_to_nas transfer modules."""
from code.file_utils import check_path_exists,  get_base_path
from code.yamlconfig_helper import replace_config_placeholder, resolve_relative_paths
from pathlib import Path


def get_flight_folder(recordings_path: Path) -> str:
    """Get the single recorded flight folder in recordings path after a flight.

    In case of multiple folders the pilot needs to be reminded to always run
    PostFlightDTT immediately after a flight, before starting a new one.

    Raises
    ------
    FileNotFoundError
        If no flight folder is found — possibly a HySpexAir recording issue.
    ValueError
        If more than one flight folder is found — PostFlightDTT was not run
        after the previous flight.
    """
    check_path_exists(
        recordings_path, message="Check that the path is correct and HySpexAir recorded correctly.")
    flight_folders = [f for f in recordings_path.iterdir() if f.is_dir()]

    if len(flight_folders) == 0:
        raise FileNotFoundError(
            f"No flight folder found in: {recordings_path}\n"
            "Check that HySpexAir recorded correctly and the path is correct."
        )
    if len(flight_folders) > 1:
        raise ValueError(
            f"Expected exactly one flight folder in: {recordings_path}\n"
            f"Found {len(flight_folders)}: {[f.name for f in flight_folders]}\n"
            "You might have started a new flight without running PostFlightDTT.exe\n"
            "You need to manually handle the data transfer in this case!"
        )

    return flight_folders[0].name


def get_resolved_config(config: dict, flight_folder: str | None = None) -> dict:
    """Replace placeholders with flight folder if available and resolve relative paths in config."""
    if flight_folder is not None:
        config = replace_config_placeholder(
            config=config,
            placeholder="{flight_folder}",
            replacement=flight_folder
        )
    resolved_config = resolve_relative_paths(
        config=config,
        base_path=get_base_path(__file__)
    )
    return resolved_config
