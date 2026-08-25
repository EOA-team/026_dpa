from osgeo import gdal
from code.file_utils import get_base_path
from enum import StrEnum
from pathlib import Path

class OrthomosaicExportFormat(StrEnum):
    GTIFF = "GTiff"
    COG = "COG"


def export_orthomosaic(
        bsq_file_path: str,
        output_file_path: str,
        export_format: OrthomosaicExportFormat):
    """
    Export an band sqeuential envi orthomosaic (*.hdr + *bsq) 
    to the specified format (GTiff or COG).

    bsq_file_path: points to the *.bsq file 
    (make sure *.hdr  is in same directory with same name as *.bsq file)

    output_file_path: path to the output file (with extension .tif or .cog)
    """

    envi_file = gdal.Open(str(bsq_file_path))

    gdal.Translate(
        output_file_path,
        envi_file,
        format=export_format.value,
        creationOptions=[
            "COMPRESS=LZW",
            "TILED=YES",
            "BIGTIFF=IF_NEEDED",
            "NUM_THREADS=ALL_CPUS"
            ]
    )

    print("Conversion complete! File saved as:", output_file_path)


if __name__ == "__main__":
    print("GDAL version:", gdal.__version__)
    envi_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.bsq"
    tif_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.tif"
    cog_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.cog"
    export_orthomosaic(envi_file_path, cog_file_path, OrthomosaicExportFormat.COG)
    


    


