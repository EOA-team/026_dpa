from harvesters.core import Harvester
import numpy as np
import matplotlib.pyplot as plt

CTI = r"C:\Program Files\Teledyne\Spinnaker\cti64\vs2015\Spinnaker_GenTL_v140.cti"

h = Harvester()
h.add_file(CTI)
h.update()

ia = h.create(search_key={"serial_number": "75006073"})
ia.start()

# ── flush old buffered frames ─────────────────────────────────
print("Flushing buffer...")
for _ in range(10):
    with ia.fetch() as buffer:
        pass  # discard

# ── grab fresh frame ──────────────────────────────────────────
print("Grabbing fresh frame...")
with ia.fetch() as buffer:
    component = buffer.payload.components[0]
    image = component.data.reshape(component.height, component.width).copy()
    print(f"✅ Frame captured!")
    print(f"   Shape: {image.shape}")
    print(f"   Dtype: {image.dtype}")
    print(f"   Min: {image.min()}  Max: {image.max()}")

ia.stop()
ia.destroy()
h.reset()

# ── Display ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(image.astype(np.float32), cmap="inferno")
plt.colorbar(im, ax=ax, label="Raw signal (counts)")
ax.set_title(f"FLIR A65 — fresh frame | min: {image.min()}  max: {image.max()}")
plt.tight_layout()
plt.show()