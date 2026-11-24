"""Control of the FLIR A65 thermal camera via Harvesters and GenTL.

The camera free-runs at CAMERA_FPS. fetch_newest() empties the frame
queue before each capture and returns the newest frame, at most one
camera frame period old.
"""

from harvesters.core import Harvester, ImageAcquirer
from pathlib import Path

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
        """Max seconds to wait for a frame after a buffer flush.

        Two capture periods - a generous ceiling: the frame normally
        arrives within one camera frame period after the flush.
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

    def disconnect(self) -> None:
        """Stop acquisition if running and release the camera connection."""
        if self._acquirer is not None:
            try:
                if self._acquirer.is_acquiring():
                    self._acquirer.stop()
                self._acquirer.destroy()
            except Exception as exc:  # noqa: PLW0718 - teardown must never fail
                print(f"[CAM] Warning during disconnect: {exc}")
        if self._harvester is not None:
            self._harvester.reset()
        print("[CAM] Disconnected.")
