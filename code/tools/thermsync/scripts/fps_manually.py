from harvesters.core import Harvester
import tifffile
from pathlib import Path
import time

CTI = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"
#CTI = r"C:\Program Files\Teledyne\Spinnaker\cti\vs2015\Spinnaker_GenTL_v140.cti"
out_dir = Path(__file__).resolve().parent

TARGET_FPS = 0.2
N_FRAMES = 10

h = Harvester()
h.add_file(CTI)
h.update()

ia = h.create(search_key={"serial_number": "75006073"})


ia.remote_device.node_map.PixelFormat.value = "Mono8"

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


interval = 1.0 / TARGET_FPS

try:
    for i in range(N_FRAMES):
        t0 = time.perf_counter()

        with ia.fetch() as buffer:
            t_fetch = time.perf_counter()
            component = buffer.payload.components[0]
            raw = component.data.reshape(component.height, component.width).copy()
            t_copy = time.perf_counter()

        fname = out_dir / f"thermal_{i:04d}.tif"
        tifffile.imwrite(fname, raw, photometric="minisblack")
        t_write = time.perf_counter()

        print(
            f"[{i:04d}] fetch={t_fetch - t0:.3f}s  copy={t_copy - t_fetch:.3f}s  write={t_write - t_copy:.3f}s  total={t_write - t0:.3f}s"
        )

        elapsed = time.perf_counter() - t0
        time.sleep(max(0, interval - elapsed))

finally:
    ia.stop()
    ia.destroy()
    h.reset()