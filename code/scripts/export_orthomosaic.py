from osgeo import gdal
from code.file_utils import get_base_path
from code.pdalgdal_helpers import export_orthomosaic
from enum import StrEnum


class OrthomosaicExportFormat(StrEnum):
    GTIFF = "GTiff"
    COG = "COG"


if __name__ == "__main__":
    print("GDAL version:", gdal.__version__)
    envi_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.bsq"
    cog_file_path = get_base_path(__file__).parent.parent / "data" / "mosaic_reflectance.cog"
    export_orthomosaic(envi_file_path, cog_file_path, OrthomosaicExportFormat.COG.value)
