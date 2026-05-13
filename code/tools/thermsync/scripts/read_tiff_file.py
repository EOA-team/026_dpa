import tifffile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

fname = Path("D:/ThermalCamera/thermal_0000.tif")

with tifffile.TiffFile(fname) as tif:
    celsius = tif.pages[0].asarray()
    tags = tif.pages[0].tags

    print(f"Shape:    {celsius.shape}")
    print(f"Dtype:    {celsius.dtype}")
    print(f"Min:      {celsius.min():.2f}°C")
    print(f"Max:      {celsius.max():.2f}°C")
    print(f"Mean:     {celsius.mean():.2f}°C")

    print("\nTIFF tags:")
    for tag in tags.values():
        print(f"  {tag.name:<30} {tag.value}")

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(celsius, cmap="inferno")
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Temperature (°C)")
ax.set_title(f"{fname.name}\n{celsius.min():.1f}°C → {celsius.max():.1f}°C")
plt.tight_layout()
plt.show()