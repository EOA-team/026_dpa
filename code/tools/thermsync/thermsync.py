"""ThermSync V3: capture FLIR A65 frames stamped with the APX GPS time.

One frame per capture tick: fetch the newest camera frame and save it as
thermal_YYYY-MM-DD_HHMMSS.mmm_UTC_raw.tif plus a per-frame camera metadata
CSV. Files are never overwritten.
"""

import threading
from datetime import datetime
from pathlib import Path

from code.file_utils import get_base_path
from code.tools.thermsync.nmea_reader import NmeaReader
from code.tools.thermsync.thermal_cam import ThermalCam
from code.yamlconfig_helper import load_config_from_yamlfile

_START_KEY = "s"


def format_utc(gps_time: datetime) -> str:
    """Format a UTC datetime as the filename time: 2026-05-21_094428.830."""
    millisecond = gps_time.microsecond // 1000
    return gps_time.strftime("%Y-%m-%d_%H%M%S.") + f"{millisecond:03d}"


def _load_config() -> dict:
    """Load config.yaml next to this script."""
    config_path = get_base_path(__file__) / "config.yaml"
    return load_config_from_yamlfile(config_path)


class QuitListener:
    """Background thread watching for the quit key on stdin (RDP-safe)."""

    def __init__(self, quit_key: str = "q") -> None:
        self._quit_key = quit_key.lower()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="QuitListener"
        )

    @property
    def quit_requested(self) -> bool:
        return self._stop_event.is_set()

    def start(self) -> None:
        self._thread.start()
        print(f"[KEY] Type <{self._quit_key.upper()}> + Enter to stop.")

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                key = input()
            except EOFError:
                return
            if key.strip().lower() == self._quit_key:
                print("[KEY] Quit requested.")
                self._stop_event.set()


def main() -> None:
    config = _load_config()
    cam = ThermalCam(
        target_fps=int(config["target_fps"]),
        out_dir=Path(config["destination_path"]),
    )

    nmea = NmeaReader()
    nmea.start()
    cam.prepare()
    cam.apply_default_config()
    cam.save_metadata_as_csv(
        cam.read_static_metadata(), "thermalcam_static_metadata"
    )
    cam.start_acquiring()
    print("Important: let the camera warm up ~10 min before sampling.")

    while input("Press <s> + Enter to start sampling: ").strip().lower() != _START_KEY:
        print("  Press s then Enter.")

    cam.set_nuc("Manual")
    print("Sampling - press <q> + Enter to stop.")
    quit_listener = QuitListener()
    quit_listener.start()


if __name__ == "__main__":
    main()
