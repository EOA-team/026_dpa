"""ThermSync V3: capture FLIR A65 frames stamped with the APX GPS time.

One frame per capture tick: fetch the newest camera frame and save it as
thermal_YYYY-MM-DD_HHMMSS.mmm_UTC_raw.tif plus a per-frame camera metadata
CSV. Files are never overwritten.
"""

import time
from code.file_utils import get_base_path
from code.tools.thermsync.nmea_reader import NmeaReader
from code.tools.thermsync.quit_listener import QuitListener
from code.tools.thermsync.thermal_cam import ThermalCam
from code.yamlconfig_helper import load_config_from_yamlfile
from datetime import datetime
from pathlib import Path

_START_KEY = "s"


def format_utc(gps_time: datetime) -> str:
    """Format a UTC datetime as the filename time: 2026-05-21_094428.830."""
    millisecond = gps_time.microsecond // 1000
    return gps_time.strftime("%Y-%m-%d_%H%M%S.") + f"{millisecond:03d}"


def _load_config() -> dict:
    """Load config.yaml next to this script."""
    config_path = get_base_path(__file__) / "config.yaml"
    return load_config_from_yamlfile(config_path)


def _capture_loop(
    cam: ThermalCam, nmea: NmeaReader, quit_listener: QuitListener
) -> int:
    """Capture frames until quit is requested; return the capture count."""
    frame_idx = 0
    while not quit_listener.quit_requested:
        t0 = time.perf_counter()

        frame = cam.fetch_newest()
        gps_time = nmea.get()
        if gps_time is None:
            timestamp = f"frame_{frame_idx:04d}"
        else:
            timestamp = format_utc(gps_time)

        cam.save_tiff(frame, f"thermal_{timestamp}_UTC_raw")
        cam.save_metadata_as_csv(
            cam.read_dynamic_metadata(),
            f"{timestamp}_thermalcam_dynamic_metadata",
        )

        loop_time = (time.perf_counter() - t0) * 1000
        print(f"[{frame_idx:04d}] {timestamp}_UTC | loop {loop_time:.0f} ms")

        frame_idx += 1
        elapsed = time.perf_counter() - t0
        time.sleep(max(0, cam.sampling_period - elapsed))
    return frame_idx


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
    cam.save_metadata_as_csv(cam.read_static_metadata(), "thermalcam_static_metadata")
    cam.start_acquiring()
    print("Important: let the camera warm up ~10 min before sampling.")

    frames = 0
    try:
        while (
            input("Press <s> + Enter to start sampling: ").strip().lower() != _START_KEY
        ):
            print("  Press s then Enter.")
        cam.set_nuc("Manual")
        print("Sampling - press <q> + Enter to stop.")
        quit_listener = QuitListener()
        quit_listener.start()
        frames = _capture_loop(cam, nmea, quit_listener)
    finally:
        cam.set_nuc("Automatic")
        cam.stop_acquiring()
        cam.disconnect()
        nmea.stop()
    print(f"Capture complete. {frames} frames saved.")


if __name__ == "__main__":
    main()
