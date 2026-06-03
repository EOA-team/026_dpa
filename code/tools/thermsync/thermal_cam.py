"""
thermal_cam.py
--------------
FLIR A65 capture via harvesters + Spinnaker GenTL CTI.

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

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
class ThermalCam:
    # GenTL producer (DLL) that bridges Harvesters to the camera hardware via the GenTL
    # standard interface. Handles device discovery, low-level communication, and data
    # transport. Without it, Harvesters has no way to talk to the camera.
    CTI_PATH = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"
    CAMERA_SERIAL = "75006073" # FLIR A65 thermal camera serial number
    CAMERA_FPS = 30 # Camera always runs with FPS=30 and streams data into buffer
    CAMERA_SAMPLING_PERIOD = float(1 / CAMERA_FPS) # 33.33ms

    def __init__(self, target_fps: int, out_dir : Path):
        self._harvester         = None
        self.image_acquirer    = None
        self._node_map          = None
        self._target_fps        = target_fps
        self._out_dir           = out_dir

    @property
    def sampling_period(self) -> float:
        return 1/self._target_fps

    @property
    def buffer_timeout(self) -> int:
        """Expect to fetch Image from Buffer latest after Sampling Period + Camera Sampling Period
        E.g. fps = 10 , tsample = 100ms , tcam_sampl = 33ms (FPS=30) """
        return self.sampling_period + self.CAMERA_SAMPLING_PERIOD

    def prepare(self):
        print(f"[CAM] Loading GenTL CTI: {self.CTI_PATH}")
        self._harvester = Harvester()
        self._harvester.add_file(self.CTI_PATH)
        self._harvester.update()

        print(f"[CAM] Connecting to camera serial {self.CAMERA_SERIAL} ...")
        self.image_acquirer = self._harvester.create(search_key={"serial_number": self.CAMERA_SERIAL})
        self._node_map = self.image_acquirer.remote_device.node_map


    def disconnect(self):
        if self.image_acquirer:
            try:
                self.image_acquirer.stop()
            except Exception as e:
                print(f"[CAM] Warning: failed to stop image acquirer: {e}")
            self.image_acquirer.destroy()
        if self._harvester:
            self._harvester.reset()
        print("[CAM] Disconnected.")

    def start_acquiring(self):
        self.image_acquirer.start()
        if self.image_acquirer.is_acquiring():

            print("[CAM] Acquisition started!")
        else:
            raise RuntimeError("[CAM] Failed to start acquisition — camera is not acquiring.")

    def stop_acquiring(self):

        self.image_acquirer.stop()
        if not self.image_acquirer.is_acquiring():
            print("[CAM] Acquisition stopped!")
        else:
            raise RuntimeError("[CAM] Failed to stop acquisition — camera is still acquiring.")


    def apply_default_config(self):
        """Apply camera settings. Called once at connect."""
        ia = self.image_acquirer
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

    @staticmethod
    def raw_to_celsius(image: np.ndarray) -> np.ndarray:
        """
        Convert raw uint16 pixel values from the FLIR A65 to degrees Celsius.

        Camera settings:
          - PixelFormat:                 Mono14
          - CMOSBitDepth:                bit14bit
          - TemperatureLinearMode:       On
          - TemperatureLinearResolution: High

        Formula (from FLIR documentation):
          T [K] = raw * 0.04
          T [°C] = T [K] - 273.15

        Args:
            image: uint16 ndarray as delivered by the camera (H x W).

        Returns:
            float32 ndarray of temperature in °C, same shape as input.
        """
        return image.astype(np.float32) * 0.04 - 273.15

    def read_config(self):
        """Read back and print current camera settings for verification."""
        ia = self.image_acquirer
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

    def set_nuc(self, mode: str):
        """Switch NUC (Non-Uniformity Correction) mode. mode = 'Automatic' or 'Manual'."""
        self._node_map.NUCMode.value = mode

    def _count_queued_frames(self) -> int:
        """Count how many frames are currently waiting in the buffer."""
        count = 0
        buffers = []
        try:
            while True:
                buffers.append(self.image_acquirer.fetch(timeout=0.05))
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
    def save_tiff(self, raw: np.ndarray, fname_stem: str,
                  save_raw: bool = True, save_celsius: bool = True):
        """
        Save frame as TIFF.
        fname_stem: filename without extension, e.g. 'thermal_2026-05-13_154532.200_UTC'
        """
        self._out_dir.mkdir(parents=True, exist_ok=True)

        if save_raw:
            tifffile.imwrite(
                self._out_dir / f"{fname_stem}_raw.tif",
                raw,
                photometric="minisblack"
            )

        if save_celsius:
            celsius = self.raw_to_celsius(raw)
            tifffile.imwrite(
                self._out_dir / f"{fname_stem}_celsius.tif",
                celsius,
                photometric="minisblack"
            )

    def fetch_metadata(self) -> dict:
        """
                Fetch meaningful metadata from the camera node map.

                Used for:
                - Post-processing: Temperature linear multiplier conversion (raw→°C) using the
                  0.04/0.4 High/Low resolution factor. Emissivity, atmospheric corrections,
                  and window transmissions are applied for precise radiometric accuracy.
                  SensorFocalLength is collected for frame stitching.
                - Device health: SensorTemperature and HousingTemperature to detect overheating
                  or thermal drift; ShutterTemperature to verify NUC functionality.

                NOTE: Because TemperatureLinearMode=On, the traditional Planck calibration
                constants (R, B, F, O) are bypassed and ignored during image conversion.

                Keys collected and their purpose:

                Camera Identity:
                    DeviceModelName         : Camera model name (e.g. 'FLIR AX5')
                    DeviceID                : Camera serial number as reported by GigE device
                    CameraSN                : Camera body serial number
                    SensorSN                : Sensor module serial number
                    CameraFirmwareVersion   : Firmware version of the camera body
                    SensorFirmwareVersion   : Firmware version of the sensor module
                    SensorFocalLength       : Lens focal length identifier (e.g. 'FL025' = 25mm)

                Thermal Calibration (Bypassed by Linear Mode, but stored for reference):
                    R, B, F, O              : Planck constants — internal factory calibration constants.
                                              Ignored during raw processing when TemperatureLinearMode=On.
                    J1                      : Radiometric gain — scaling factor for the signal (Ignored).
                    RThg                    : Planck R constant for high gain mode specifically (Ignored).

                Radiometric Environment Corrections (Still active and required):
                    ObjectEmissivity        : Emissivity of the target surface (1.0 = perfect blackbody)
                    ReflectedTempInternal   : Reflected apparent temperature (scaled: Value / 100 = °C) —
                                              compensates for background radiation reflected off the target
                    AtmTempInternal         : Atmospheric temperature (scaled: Value / 100 = °C) —
                                              corrects for absorption by air between camera and target
                    AtmosphericTransmission : Fraction of radiation transmitted through atmosphere (0-1)
                    WindowTransmission      : Fraction of radiation transmitted through IR window (0-1)
                    WindowTempInternal      : IR window temperature (scaled: Value / 100 = °C) —
                                              compensates for radiation emitted by the window itself

                Sensor Temperatures (Camera health and drift monitoring):
                    SensorTemperature       : Temperature of the IR sensor chip in °C —
                                              affects calibration drift; monitors core stability
                    HousingTemperature      : Temperature of the camera housing in °C —
                                              indicator of thermal stability of the outer camera body
                    ShutterTemperature      : Temperature of the internal shutter in Kelvin —
                                              used as reference during NUC (Non-Uniformity Correction)

                Acquisition Settings (Defines raw pixel data interpretation):
                    PixelFormat             : Pixel encoding format (e.g. 'Mono14' = 14-bit monochrome)
                    CMOSBitDepth            : Bit depth of the CMOS sensor output (e.g. 'bit14bit')
                    SensorGainMode          : Gain setting — HighGainMode (bounds range to approx. -25°C to 135°C),
                                              LowGainMode for hot scenes with wider temperature range
                    TemperatureLinearMode   : 'On' — Forces pixel values to scale linearly with absolute temperature (Kelvin)
                    TemperatureLinearResolution : 'High' = 0.04 Kelvin/DN multiplier, 'Low' = 0.4 Kelvin/DN multiplier.
                                              Formula: °C = (Raw_Pixel * Resolution_Multiplier) - 273.15
                    NUCMode                 : Non-Uniformity Correction mode — 'Automatic' means camera
                                              self-corrects periodically using the internal shutter
                    SensorFrameRate         : Frame rate setting of the sensor ('Fast' = 30fps/60fps, 'Slow' = 9fps)

                Live Reading (Sanity check):
                    Spot                    : Current center-pixel spot temperature in °C —
                                              useful to verify custom script calculations match camera firmware
        """
        nm = self._node_map

        KEYS = [
            "DeviceModelName", "DeviceID", "CameraSN", "SensorSN",
            "CameraFirmwareVersion", "SensorFirmwareVersion", "SensorFocalLength",
            "R", "B", "F", "O", "J1", "RThg",
            "ObjectEmissivity",
            "ReflectedTempInternal", "AtmTempInternal",
            "AtmosphericTransmission", "WindowTransmission", "WindowTempInternal",
            "SensorTemperature", "HousingTemperature", "ShutterTemperature",
            "PixelFormat", "CMOSBitDepth", "SensorGainMode",
            "TemperatureLinearMode", "TemperatureLinearResolution",
            "NUCMode", "SensorFrameRate", "Spot",
        ]

        metadata = {"timestamp": datetime.now(timezone.utc).isoformat()}

        for key in KEYS:
            try:
                metadata[key] = getattr(nm, key).value
            except Exception:
                metadata[key] = None

        return metadata

if __name__ == "__main__":
    cam = ThermalCam(target_fps=1, out_dir= Path("D:/ThermalCamera"))
    print(cam.sampling_period)
    print(cam.buffer_timeout)
    cam.prepare()
    cam.apply_default_config()

    print(cam.fetch_metadata())
    # cam.start_acquiring()
    #
    #
    # for i in range(10):
    #     t0 = time.perf_counter()
    #     with cam.image_acquirer.fetch(timeout=cam.buffer_timeout) as buffer:
    #         t_fetch = time.perf_counter()
    #         component = buffer.payload.components[0]
    #         raw = component.data.reshape(component.height, component.width).copy()
    #         t_copy = time.perf_counter()
    #
    #     celsius = ThermalCam.raw_to_celsius(raw)
    #
    #     fname = cam._out_dir / f"thermal_{i:04d}.tif"
    #     fname.parent.mkdir(parents=True, exist_ok=True)
    #     tifffile.imwrite(fname, celsius, photometric="minisblack")
    #     t_write = time.perf_counter()
    #
    #     print(
    #         f"[{i:04d}] fetch={t_fetch - t0:.3f}s  copy={t_copy - t_fetch:.3f}s  write={t_write - t_copy:.3f}s  total={t_write - t0:.3f}s"
    #     )
    #
    #     elapsed = time.perf_counter() - t0
    #     additional_wait = cam.sampling_period - elapsed
    #     time.sleep(max(0, additional_wait))  # Do not wait when value already negative
    #
    #     print("elapsed time:", elapsed)
    #     print("waiting time:", additional_wait)
    #     print("sampling period", cam.sampling_period)
    #
    #
    # #Now here ask for start sampling
    # cam.stop_acquiring()
    # cam.disconnect()