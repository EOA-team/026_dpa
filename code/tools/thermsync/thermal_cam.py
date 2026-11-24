"""Control of the FLIR A65 thermal camera via Harvesters and GenTL.

The camera free-runs at CAMERA_FPS. fetch_newest() discards the old
frames waiting in the queue before each capture and returns the newest
frame, at most one camera frame period old.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import tifffile
from genicam.gentl import GenTL_GenericException
from harvesters.core import Harvester, ImageAcquirer

CAMERA_FPS = 30  # the A65 always streams at this fixed rate
CAMERA_SERIAL = "75006073"  # serial of this camera, used to find it
CAMERA_FRAME_PERIOD_S = 1.0 / CAMERA_FPS

CTI_PATH = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"

_NUM_BUFFERS = 3  # Spinnaker's minimum; the engine reserves one, leaving 2 stored frames

_CAMERA_SETTINGS = {
    "PixelFormat": "Mono14",
    "CMOSBitDepth": "bit14bit",
    "SensorGainMode": "HighGainMode",
    "TemperatureLinearMode": "On",
    "TemperatureLinearResolution": "High",
    "AcquisitionMode": "Continuous",
    "CounterTriggerSource": "Off",
    "NUCMode": "Automatic",
}

_STATIC_METADATA_KEYS = (
    "DeviceModelName", "DeviceID", "CameraSN", "SensorSN",
    "CameraFirmwareVersion", "SensorFirmwareVersion", "SensorFocalLength",
    "R", "B", "F", "O", "J1", "RThg",
    "ObjectEmissivity",
    "ReflectedTempInternal", "AtmTempInternal",
    "AtmosphericTransmission", "WindowTransmission", "WindowTempInternal",
    "PixelFormat", "CMOSBitDepth", "SensorGainMode",
    "TemperatureLinearMode", "TemperatureLinearResolution",
    "SensorFrameRate",
)

_DYNAMIC_METADATA_KEYS = (
    "SensorTemperature", "HousingTemperature", "ShutterTemperature",
    "Spot", "NUCMode",
)


class ThermalCam:
    """FLIR A65 control: connection, configuration, frame capture, metadata."""

    def __init__(self, target_fps: int, out_dir: Path) -> None:
        self._target_fps = target_fps
        self._out_dir = out_dir
        self._harvester: Harvester | None = None
        self._acquirer: ImageAcquirer | None = None
        self._node_map = None  # GenICam feature map, set in prepare()

    @property
    def sampling_period(self) -> float:
        """Seconds between capture ticks: 1 / target_fps."""
        return 1.0 / self._target_fps

    @property
    def buffer_timeout(self) -> float:
        """Max seconds to wait for a frame after the old frames are discarded.

        Two capture periods - a generous ceiling: the frame normally
        arrives within one camera frame period after discarding.
        """
        return self.sampling_period * 2

    def prepare(self) -> None:
        """Connect to the camera: load the GenTL producer, find it by serial."""
        print(f"[CAM] Loading GenTL CTI: {CTI_PATH}")
        self._harvester = Harvester()
        self._harvester.add_file(CTI_PATH)
        self._harvester.update()
        print(f"[CAM] Connecting to camera serial {CAMERA_SERIAL} ...")
        self._acquirer = self._harvester.create(
            search_key={"serial_number": CAMERA_SERIAL}
        )
        self._node_map = self._acquirer.remote_device.node_map
        print("[CAM] Camera connected.")

    def apply_default_config(self) -> None:
        """Apply the radiometric acquisition settings."""
        self._acquirer.num_buffers = _NUM_BUFFERS
        for name, value in _CAMERA_SETTINGS.items():
            getattr(self._node_map, name).value = value
        print("[CAM] Default config applied.")

    def start_acquiring(self) -> None:
        """Start the continuous frame stream into the driver buffer."""
        self._acquirer.start()
        if not self._acquirer.is_acquiring():
            raise RuntimeError("camera did not start acquiring")
        print("[CAM] Acquisition started.")

    def stop_acquiring(self) -> None:
        """Stop the frame stream."""
        self._acquirer.stop()
        if self._acquirer.is_acquiring():
            raise RuntimeError("camera is still acquiring")
        print("[CAM] Acquisition stopped.")

    def set_nuc(self, mode: str) -> None:
        """Set the NUC mode, e.g. "Manual" during sampling, "Automatic" after."""
        self._node_map.NUCMode.value = mode

    def fetch_newest(self):
        """Return the frame produced right now: discard old ones, then fetch."""
        self._discard_old_frames()
        with self._acquirer.fetch(timeout=self.buffer_timeout) as buffer:
            component = buffer.payload.components[0]
            frame = component.data.reshape(component.height, component.width).copy()
        return frame

    def _discard_old_frames(self) -> None:
        """Throw away all frames waiting in the queue.

        Each discarded frame's buffer is returned to the pool, ready for the
        next frame the camera produces. The empty-check waits only half a
        frame period, so the loop always ends before the next fresh frame
        arrives.
        """
        empty_check_timeout = CAMERA_FRAME_PERIOD_S / 2
        while True:
            old_frame = self._acquirer.try_fetch(timeout=empty_check_timeout)
            if old_frame is None:
                return
            old_frame.queue()

    def read_static_metadata(self) -> dict:
        """Read identity, calibration and radiometric settings (unchanging).

        Read once per session. The returned dict carries a "timestamp" row
        recording when the session metadata was taken.
        """
        metadata = {"timestamp": datetime.now(timezone.utc).isoformat()}
        metadata.update(self._read_metadata_keys(_STATIC_METADATA_KEYS))
        return metadata

    def read_dynamic_metadata(self) -> dict:
        """Read the per-frame health values: temperatures, spot reading, NUC mode."""
        return self._read_metadata_keys(_DYNAMIC_METADATA_KEYS)

    def _read_metadata_keys(self, keys: tuple) -> dict:
        """Read the given GenICam features from the camera node map."""
        return {key: getattr(self._node_map, key).value for key in keys}

    def save_tiff(self, frame, filename: str) -> None:
        """Save the frame as filename.tif; never overwrite an existing file."""
        file_path = self._prepare_save_path(filename, "tif")
        if file_path is None:
            return
        tifffile.imwrite(file_path, frame, photometric="minisblack")

    def save_metadata_as_csv(self, metadata: dict, filename: str) -> None:
        """Write metadata as key,value rows; never overwrite an existing file."""
        file_path = self._prepare_save_path(filename, "csv")
        if file_path is None:
            return
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["parameter", "value"])
            for key, value in metadata.items():
                writer.writerow([key, value])

    def _prepare_save_path(self, filename: str, extension: str) -> Path | None:
        """Return the path to write to, or None if the file already exists."""
        self._out_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._out_dir / f"{filename}.{extension}"
        if file_path.exists():
            print(f"[CAM] {file_path.name} already exists - skipped")
            return None
        return file_path

    def disconnect(self) -> None:
        """Stop acquisition if running and release the camera connection."""
        if self._acquirer is not None:
            try:
                if self._acquirer.is_acquiring():
                    self._acquirer.stop()
                self._acquirer.destroy()
            except (GenTL_GenericException, OSError) as exc:
                print(f"[CAM] Warning during disconnect: {exc}")
        if self._harvester is not None:
            self._harvester.reset()
        print("[CAM] Disconnected.")
