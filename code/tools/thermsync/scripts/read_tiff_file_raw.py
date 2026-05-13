import tifffile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

fname = Path("D:/HySpexAir/Recordings/ThermalCamera/thermal_2026-05-13_173609.200_UTC_raw.tif")

with tifffile.TiffFile(fname) as tif:
    raw = tif.pages[0].asarray()
    tags = tif.pages[0].tags

    print(f"Shape:    {raw.shape}")
    print(f"Dtype:    {raw.dtype}")
    print(f"Raw Min:  {raw.min()}")
    print(f"Raw Max:  {raw.max()}")

    print("\nTIFF tags:")
    for tag in tags.values():
        print(f"  {tag.name:<30} {tag.value}")

# convert to celsius
celsius = raw.astype(np.float32) * 0.04 - 273.15

print(f"\nTemperature range: {celsius.min():.2f}°C → {celsius.max():.2f}°C")
print(f"Mean temperature:  {celsius.mean():.2f}°C")

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(celsius, cmap="inferno")
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Temperature (°C)")
ax.set_title(f"{fname.name}\n{celsius.min():.1f}°C → {celsius.max():.1f}°C")
plt.tight_layout()
plt.show()