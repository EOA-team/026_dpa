from osgeo import gdal
import pdal
import json
import re
from pathlib import Path

gdal.UseExceptions()  # explicitly enable exceptions (recommended)

def las_to_geotif(
        input_las:  Path,
        output_tif: Path,
        resolution: float = 0.05,
) -> None:
    """Convert a LAS point cloud to a DSM GeoTIFF using PDAL.

    Uses per-cell maximum Z binning (writers.gdal, output_type='max').
    At 0.05m resolution this is equivalent in practice to the TIN interpolation
    used by the QGIS 'Export raster (using triangulation)' tool.

    Note: Need to validate with ReSe if this is fine

    Args:
        input_las:   Path to the input .las file.
        output_tif:  Path to the output .tif file.
        resolution:  Raster resolution in meters (default: 0.05m).
    """
    output_tif.parent.mkdir(parents=True, exist_ok=True)

    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            str(input_las),
            {
                "type": "writers.gdal",
                "filename": str(output_tif),
                "resolution": resolution,
                "output_type": "max",       # DSM = highest point per cell
                "data_type": "float32",     # match expected ENVI data type 4
                "gdalopts": "COMPRESS=LZW",
            }
        ]
    }))

    pipeline.execute()
    print(f"DSM created: {output_tif}")

def _rename_envi_bin(bin_file: Path, output_file: Path) -> None:
    """Rename GDAL-generated .bin file to the desired output filename (no extension).

    GDAL's ENVI driver always appends .bin to the data file. This renames it
    to match the intended output name while leaving the .hdr file untouched.

    Args:
        bin_file:    Path to the .bin file created by GDAL.
        output_file: Desired output path (no extension).
    """
    bin_file.rename(output_file)

def geotiff_to_envi_dsm(
        input_tif:   Path,
        output_file: Path,
) -> None:
    """Convert a GeoTIFF DSM to ENVI format, producing <output_file> and <output_file>.hdr.

    GDAL's ENVI driver creates <name>.bin and <name>.hdr by default.
    The .bin file is renamed to <output_file> (no extension) after creation.

    Args:
        input_tif:   Path to the input GeoTIFF file.
        output_file: Path to the output ENVI file (without extension, e.g. .../DSM).
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    src = gdal.Open(str(input_tif))
    if src is None:
        raise FileNotFoundError(f"Could not open: {input_tif}")

    tmp_file = output_file.parent / f"{output_file.name}.bin"
    gdal.Translate(
        str(tmp_file),
        src,
        format="ENVI",
        creationOptions=["INTERLEAVE=BSQ"],
    )
    src = None  # close file

    _rename_envi_bin(tmp_file, output_file)
    print(f"ENVI DSM created: {output_file} + {output_file.name}.hdr")


def fix_envi_header(hdr_file: Path) -> None:
    """Patch GDAL-generated ENVI header to match PARGE's expected format.

    Fixes the following differences vs PARGE output:
        - interleave: uppercase BSQ
        - map info: formats coordinates, resolution to 9 decimals, adds units=Meter
        - coordinate system string: removes {} wrapper and VERTCS block
        - sensor type: adds before byte order if missing
        - adds x start, y start, pixel size
        - removes band names, data ignore value, default bands

    Args:
        hdr_file: Path to the .hdr file to fix.
    """
    text = hdr_file.read_text()

    # Fix interleave to uppercase
    text = re.sub(r"interleave = bsq", "interleave = BSQ", text)

    # Fix map info: remove spaces, format resolution to 9 decimals, add units=Meter
    def fix_map_info(match: re.Match) -> str:
        parts = [p.strip() for p in match.group(1).split(",")]
        x, y, res = float(parts[3]), float(parts[4]), float(parts[5])
        res_str = f"{res:.9f}"
        return f"map info = {{UTM,1,1,{x:.3f},{y:.3f}, {res_str}, {res_str},32,North,WGS-84,units=Meter}}"

    text = re.sub(r"map info = \{(.*?)\}", fix_map_info, text)

    # Fix coordinate system string: remove {} wrapper and VERTCS block
    text = re.sub(r"coordinate system string = \{(.*?),VERTCS\[.*?\]\}",
                  r"coordinate system string = \1", text, flags=re.DOTALL)

    # Add sensor type before byte order if missing
    if "sensor type" not in text:
        text = re.sub(r"(byte order = 0\n)", "sensor type = \n\\1", text)

    # Move sensor type before byte order
    text = re.sub(r"(byte order = 0\n)(sensor type = \n)", r"\2\1", text)

    # Add x start, y start after byte order
    if "x start" not in text:
        text = re.sub(r"(byte order = 0\n)", "\\1x start =  1\ny start =  1\n", text)

    # Add pixel size after coordinate system string
    res_match = re.search(r"map info = \{UTM,1,1,[\d.]+,[\d.]+, ([\d.]+),", text)
    if res_match and "pixel size" not in text:
        res_str = f"{float(res_match.group(1)):.9f}"
        text = re.sub(
            r"(coordinate system string = .*?\]\])\n",
            f"\\1\npixel size = {{{res_str}, {res_str}}}\n",
            text, flags=re.DOTALL
        )

    # Remove band names, data ignore value, default bands
    text = re.sub(r"band names = \{.*?\}\n", "", text, flags=re.DOTALL)
    text = re.sub(r"data ignore value = .*?\n", "", text)
    text = re.sub(r"default bands = \{.*?\}\n", "", text)

    hdr_file.write_text(text)

if __name__ == "__main__":
    # Example usage:
    las_to_geotif(
        input_las=Path("E:/dsm_creation_test/Mission 1_lidardump-2025.09.03-14.02.28.las"),
        output_tif=Path("E:/dsm_creation_test/DSM.tif"),
        resolution=0.05
    )

    geotiff_to_envi_dsm(
        input_tif=Path("E:/dsm_creation_test/DSM.tif"),
        output_file=Path("E:/dsm_creation_test/DSM")
    )

    fix_envi_header(Path("E:/dsm_creation_test/DSM.hdr"))

    

