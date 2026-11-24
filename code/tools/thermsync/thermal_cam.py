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
