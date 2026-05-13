"""
thermal_cam.py
--------------
FLIR A65 capture via harvesters + Spinnaker GenTL CTI.

Handles:
  - camera init and fixed config
  - FFC (Flat Field Correction) auto <-> manual switching
  - adjustable frame rate
  - per-frame TIFF saving with GNSS timestamp + device temperatures
  - raw_to_celsius() helper for post-processing

Usage (via main.py):
    cam = ThermalCam()
    cam.connect()
    cam.set_fps(5)
    cam.start_capture(nmea_reader)   # locks FFC to Manual
    # ... running ...
    cam.stop_capture()               # unlocks FFC to Auto
    cam.disconnect()

Links:
https://www.flir.com/support-center/instruments2/how-do-i-manually-control-the-nuc-auto-calibration-in-the-flir-a35-and-a65/
https://www.flir.com/support-center/instruments2/how-do-i-configure-my-camera-to-stream-a-temperature-linear-signal/
"""

import time
import threading
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
import tifffile
from harvesters.core import Harvester
from code.yamlconfig_helper import load_config_from_yamlfile
from code.file_utils import get_base_path

config_path = get_base_path(__file__) / "config.yaml"
config = load_config_from_yamlfile(config_path)


# GenTL producer (DLL) that bridges Harvesters to the camera hardware via the GenTL
# standard interface. Handles device discovery, low-level communication, and data
# transport. Without it, Harvesters has no way to talk to the camera.
CTI_PATH      = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"


OUTPUT_ROOT   = Path("recordings") / "thermal"


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
class ThermalCam:
    # GenTL producer (DLL) that bridges Harvesters to the camera hardware via the GenTL
    # standard interface. Handles device discovery, low-level communication, and data
    # transport. Without it, Harvesters has no way to talk to the camera.
    CTI_PATH = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"
    CAMERA_SERIAL = "75006073" # FLIR A65 thermal camera serial number
    CAMERA_FPS = 30
    CAMERA_SAMPLING_PERIOD = 1 / CAMERA_FPS # 33.33ms

    def __init__(self):
        self._harvester         = None
        self._image_acquirer    = None
        self._node_map          = None
        self._fps               = None
        self._out_dir           = None

    def prepare(self):
        print(f"[CAM] Loading GenTL CTI: {CTI_PATH}")
        self._harvester = Harvester()
        self._harvester.add_file(CTI_PATH)
        self._harvester.update()

        print(f"[CAM] Connecting to camera serial {self.CAMERA_SERIAL} ...")
        self._image_acquirer = self._harvester.create(search_key={"serial_number": self.CAMERA_SERIAL})
        self._node_map = self._image_acquirer.remote_device.node_map
        print("[CAM] Connected. Camera warming up in Auto FFC mode.")
        print("[CAM] Wait 2–5 minutes before starting capture.")


    def disconnect(self):
        if self._image_acquirer:
            try:
                self._image_acquirer.stop()
            except Exception as e:
                print(f"[CAM] Warning: failed to stop image acquirer: {e}")
            self._image_acquirer.destroy()
        if self._harvester:
            self._harvester.reset()
        print("[CAM] Disconnected.")

    def start_acquiring(self):
        self._image_acquirer.start()
        print(self._image_acquirer.is_acquiring())
        if self._image_acquirer.is_acquiring():

            print("[CAM] Acquisition started successfully.")
        else:
            raise RuntimeError("[CAM] Failed to start acquisition — camera is not acquiring.")

    def stop_acquiring(self):
        self._image_acquirer.stop()
        if not self._image_acquirer.is_acquiring():
            print("[CAM] Acquisition stopped successfully.")
        else:
            raise RuntimeError("[CAM] Failed to stop acquisition — camera is still acquiring.")


    def apply_default_config(self):
        """Apply camera settings. Called once at connect."""
        ia = self._image_acquirer
        ia.num_buffers                       = 3

        nm = self._node_map
        nm.PixelFormat.value                 = "Mono14"
        nm.CMOSBitDepth.value                = "bit14bit"
        nm.SensorGainMode.value              = "HighGainMode"
        nm.TemperatureLinearMode.value       = "On"
        nm.TemperatureLinearResolution.value = "High"
        nm.AcquisitionMode.value             = "Continuous"
        nm.CounterTriggerSource.value        = "Off"
        nm.NUCMode.value                     = "Automatic"

    def read_config(self):
        """Read back and print current camera settings for verification."""
        ia = self._image_acquirer
        nm = self._node_map
        settings = {
            "num_buffers": ia.num_buffers,
            "PixelFormat": nm.PixelFormat.value,
            "CMOSBitDepth": nm.CMOSBitDepth.value,
            "SensorGainMode": nm.SensorGainMode.value,
            "TemperatureLinearMode": nm.TemperatureLinearMode.value,
            "TemperatureLinearResolution": nm.TemperatureLinearResolution.value,
            "AcquisitionMode": nm.AcquisitionMode.value,
            "CounterTriggerSource": nm.CounterTriggerSource.value,
            "NUCMode": nm.NUCMode.value,
            "SensorFrameRate": nm.SensorFrameRate.value,
        }
        print("[CAM] Current camera settings:")
        for k, v in settings.items():
            print(f"  {k:<30} {v}")
        return settings


    def set_fps(self, fps: float):
        """Set the target capture rate. Can be called before start_capture."""
        if fps <= 0:
            print("[CAM] ⚠ FPS must be > 0. Ignoring.")
            return
        self._fps = fps
        print(f"[CAM] FPS set to {fps}")

    def _set_ffc(self, mode: str):
        """Switch FFC mode. mode = 'Auto' or 'Manual'."""
        self._node_map.FFCMode.value = mode
        print(f"[CAM] FFC mode → {mode}")

    def _count_queued_frames(self) -> int:
        """Count how many frames are currently waiting in the buffer."""
        count = 0
        buffers = []
        try:
            while True:
                buffers.append(self._image_acquirer.fetch(timeout=0.05))
                count += 1
        except Exception as e:
            print(f"[CAM] ⚠ Buffer exhausted after {count} frame(s): {e}")
        finally:
            for b in buffers:
                b.queue()  # return all buffers unconsumed
        return count




    # ------------------------------------------------------------------
    # Per-frame device temperatures
    # ------------------------------------------------------------------
    def _read_temperatures(self) -> dict:
        """
        Read per-frame device temperatures from camera node map.
        Node names match FLIR A65 GenICam XML — verify on first connect.
        Returns dict with values in °C (as reported by camera).
        """
        nm = self._nm
        out = {}
        for key in ("SensorTemperature", "DeviceTemperature", "HousingTemperature"):
            try:
                out[key] = getattr(nm, key).value
            except Exception:
                out[key] = None   # node may not exist — verify on device
        return out

    # ------------------------------------------------------------------
    # TIFF saving
    # ------------------------------------------------------------------
    def _save_tiff(
        self,
        raw: np.ndarray,
        gps_time: datetime,
        lag_ms: float,
        temps: dict,
        frame_idx: int,
    ):
        """
        Save raw uint16 frame as TIFF.

        Filename:  thermal_2025-06-10_104532.120_UTC.tif
        ImageDescription tag contains GPS timestamp + sync lag.
        Extra TIFF tags carry device temperatures.

        Pixels are saved as raw uint16.
        Apply raw_to_celsius() in post-processing.
        """
        ts_str  = gps_time.strftime("%Y-%m-%d_%H%M%S.") + f"{gps_time.microsecond // 1000:03d}"
        fname   = self._out_dir / f"thermal_{ts_str}_UTC.tif"

        description = (
            f"gps_time={gps_time.isoformat()} "
            f"synchronization_lag={lag_ms:.1f}ms "
            f"SensorTemperature={temps.get('SensorTemperature')} "
            f"DeviceTemperature={temps.get('DeviceTemperature')} "
            f"HousingTemperature={temps.get('HousingTemperature')}"
        )

        tifffile.imwrite(
            fname,
            raw,
            photometric="minisblack",
            description=description,
        )

        print(f"[CAM] #{frame_idx:04d}  {fname.name}  lag={lag_ms:.1f}ms")

if __name__ == "__main__":
    cam = ThermalCam()
    cam.prepare()
    cam.apply_default_config()
    cam.start_acquiring()
    #Now here ask for start sampling
    cam.stop_acquiring()
    cam.disconnect()