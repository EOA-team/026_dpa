"""
This script visualizes the GCP accuracy of re112o_250918.
It was processed with 3 different Stabilized Mount settings:
- "None": No stabilization, using raw sensor data.
- "SynthesizeGimbal": Synthesizes gimbal data to approximate stabilization.
- "StabilizedMount": Model-based stabilization

Compared with HyperCover as baseline.

Files can be found on Drone Station: E:\00_Tests\260526_DPA_Accuracy_Different_Settings
"""


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

file_path = Path(__file__).parent

CSV_PATH = file_path / "260526_gcp_accuracy.csv"

df = pd.read_csv(CSV_PATH, sep = ";")
df = df[df["GCP"].apply(lambda x: str(x).isdigit())].copy()

cols = {
    "Model =StabilizedMount[m]": "StabilizedMount",
    "None[m]": "None",
    "SynthesizeGimbal[m]": "SynthesizeGimbal",
    "HyperCover[m]": "HyperCover",
}

data = [df[col].astype(float).values for col in cols.keys()]
labels = list(cols.values())
colors = ["#534AB7", "#1D9E75", "#D85A30", "#BA7517"]

fig, ax = plt.subplots(figsize=(9, 5))

bp = ax.boxplot(
    data,
    patch_artist=True,
    widths=0.45,
    medianprops=dict(color="white", linewidth=2),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
    flierprops=dict(marker="o", markersize=5, linestyle="none"),
)

for patch, color, flier in zip(bp["boxes"], colors, bp["fliers"]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
    flier.set_markerfacecolor(color)
    flier.set_markeredgecolor(color)

for i, (whisker_pair, cap_pair) in enumerate(
    zip(zip(bp["whiskers"][::2], bp["whiskers"][1::2]),
        zip(bp["caps"][::2], bp["caps"][1::2]))
):
    for w in whisker_pair:
        w.set_color(colors[i])
    for c in cap_pair:
        c.set_color(colors[i])

ax.set_xticks([1, 2, 3, 4])
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("GCP Error (m)", fontsize=11)
ax.set_title("GCP Error by Stabilized Mount Setting", fontsize=13, fontweight="normal")
ax.yaxis.grid(True, linestyle="--", alpha=0.5)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

for i, (d, color) in enumerate(zip(data, colors), start=1):
    ax.plot(i, d.mean(), marker="D", color="white", markersize=6,
            markeredgecolor=color, markeredgewidth=1.5, zorder=5)

legend_handles = [
    mpatches.Patch(facecolor=c, alpha=0.7, label=f"{l}  (mean={d.mean():.3f}m)")
    for c, l, d in zip(colors, labels, data)
]
ax.legend(handles=legend_handles, fontsize=9, frameon=False, loc="upper right")

plt.tight_layout()
plt.show()
