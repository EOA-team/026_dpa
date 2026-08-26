"""Translate ENVI (.bsq + .hdr) to a tiled, BAND-interleaved GeoTIFF.
Note: COG Driver is buggy in GDAL 3.12 and freezes!"""
from osgeo import gdal
from code.file_utils import get_base_path
from enum import StrEnum
from pathlib import Path


gdal.UseExceptions()  # recommended: errors raise exceptions instead of just printing ERROR 1:


class OrthomosaicFormats(StrEnum):
    GTIFF = "GTiff"
    ENVI = "ENVI"


def envi_to_geotiff(bsq_file_path: str, output_file_path: str) -> gdal.Dataset:
    """
    Export ENVI (.bsq + .hdr) to a tiled, BAND-interleaved GeoTIFF.
    Make sure all metadata is preserved through COPY_SRC_MDD=YES option.
    """
    envi_file = gdal.Open(str(bsq_file_path))
 
    options = [
        "-of", "GTiff",      
        "-co", "COMPRESS=LZW", # Lossless is standard in GIS analysis 
        "-co", "TILED=YES", # Allows for instant spatial queries with Rasterio
        "-co", "BLOCKXSIZE=512",   # Set tile width to 512 (COG Standard)
        "-co", "BLOCKYSIZE=512",   # Set tile height to 512 (COG Standard)
        "-co", "BIGTIFF=IF_NEEDED", # Protection against >4GB crashes (gtiff limit is 4GB)
        "-co", "NUM_THREADS=ALL_CPUS", # MAke sure to use all threads for speed
        "-co", "INTERLEAVE=BAND", # Interleave= Best for per band statistics | Interleave= PIXEL is best for visualization (RGB)
        "-co", "COPY_SRC_MDD=YES",   # copy through all source metadata domains verbatim
        # Note : GDAL Triggers resampling only if pixel size changes --> no need to define resampling method here.
    ]

    out=gdal.Translate(
        output_file_path,
        envi_file,
        options=options,
        callback=gdal.TermProgress_nocb, #Show Progress
    )
    envi_file = None  # close file
    return out 


if __name__ == "__main__":
    print("GDAL version:", gdal.__version__)
    envi_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.bsq"
    tif_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.tif"
    cog_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.cog"

    geotif = envi_to_geotiff(envi_file_path, tif_file_path)
