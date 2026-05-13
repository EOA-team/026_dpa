from os import mkdir

from harvesters.core import Harvester
import tifffile
from pathlib import Path
import time

CTI = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"
out_dir = Path("D:\ThermalCamera")

# Constants given By Camera
CAMERA_FPS = 30 # The Camera is sampled with 30FPS, cannot be set!
CAMERA_SAMPLING_PERIOD = 1/ CAMERA_FPS

# Can be adjusted
TARGET_FPS = 1
N_FRAMES = 20

h = Harvester()
h.add_file(CTI)
h.update()


ia = h.create(search_key={"serial_number": "75006073"})
print("Buffer count:", ia.num_buffers) # Comes by default with 3 Buffers , so the oldes image in buffer is at max 66.6667 ms off
# And the time to fetch the

ia.remote_device.node_map.PixelFormat.value = "Mono8"


print("Buffer count:", ia.num_buffers)

nm = ia.remote_device.node_map
nm.SensorGainMode.value              = "HighGainMode"
nm.TemperatureLinearMode.value       = "On"
nm.TemperatureLinearResolution.value = "High"
nm.AcquisitionMode.value             = "Continuous"
nm.NUCMode.value                     = "Automatic"

# Read back to confirm
print("SensorGainMode:              ", nm.SensorGainMode.value)
print("TemperatureLinearMode:       ", nm.TemperatureLinearMode.value)
print("TemperatureLinearResolution: ", nm.TemperatureLinearResolution.value)
print("AcquisitionMode:             ", nm.AcquisitionMode.value)
print("NUCMode:                     ", nm.NUCMode.value)
print("SensorFrameRate:             ", nm.SensorFrameRate.value)



ia.start()

sampling_period  = 1.0 / TARGET_FPS
buffer_timeout = sampling_period + CAMERA_SAMPLING_PERIOD # e.g. 1s + 33.33ms

try:
    for i in range(N_FRAMES):
        t0 = time.perf_counter()

        with ia.fetch(timeout = buffer_timeout) as buffer: # If no image fetched within this time, something went wrong
            t_fetch = time.perf_counter()
            component = buffer.payload.components[0]
            raw = component.data.reshape(component.height, component.width).copy()
            t_copy = time.perf_counter()

        fname = out_dir / f"thermal_{i:04d}.tif"
        fname.parent.mkdir(parents=True, exist_ok=True)
        tifffile.imwrite(fname, raw, photometric="minisblack")
        t_write = time.perf_counter()

        print(
            f"[{i:04d}] fetch={t_fetch - t0:.3f}s  copy={t_copy - t_fetch:.3f}s  write={t_write - t_copy:.3f}s  total={t_write - t0:.3f}s"
        )

        elapsed = time.perf_counter() - t0
        additional_wait = sampling_period - elapsed
        time.sleep(max(0, additional_wait)) # Do not wait when value already negative
        print("elapsed time:", elapsed)
        print("waiting time:", additional_wait)
        print("sampling period", sampling_period)

finally:
    ia.stop()
    ia.destroy()
    h.reset()