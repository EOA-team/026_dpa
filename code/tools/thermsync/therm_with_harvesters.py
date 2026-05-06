from harvesters.core import Harvester
import numpy as np

CTI = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"

h = Harvester()
h.add_file(CTI)
h.update()

# connect to FLIR AX5 by serial number
ia = h.create_image_acquirer(serial_number="75006073")
ia.start()

print("Grabbing frame...")
with ia.fetch() as buffer:
    component = buffer.payload.components[0]
    image = component.data.reshape(component.height, component.width)
    print(f"✅ Frame captured!")
    print(f"   Shape: {image.shape}")
    print(f"   Dtype: {image.dtype}")
    print(f"   Min: {image.min()}  Max: {image.max()}")

ia.stop()
ia.destroy()
h.reset()