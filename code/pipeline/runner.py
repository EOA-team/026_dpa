"""In the future there will be many different runner scripts for different pipelines
At The moment at Agroscope we only use one default pipeline but in Future there will be
different pipelines!
Example:
 default_pipeline_runner.py
 high_accuracy_pipeline_runner.py # using georeferencing and additional corrections
 fast_processing_pipeline_runner.py # using only essential steps for fast processing
 etc.
"""

from code.file_utils import get_base_path
from code.pipeline.base import Path, PipelineFolder
from code.pipeline.steps import (
    ApxCleaning,
    BinaryToRadiance,
    BuildDigitalSurfaceModel,
    CopyFiles,
    CopyJobFolders,
    CreateRadianceOrthomosaic,
    CreateReflectanceOrthomosaic,
    FetchNavigationFiles,
    Geocoding,
    GeoreferenceSensors,
    MoveFiles,
    NavigationDiscretization,
    OrthomosaicToGeoTiff,
    ScrapeBaseStationData,
)
from datetime import timedelta
from enum import StrEnum


class AvailableTrials(StrEnum):
    """Available trials for processing, ensures type safety and avoids typos.
    Note: Will extend in the future with more trials"""

    ZOFE = "ZOFE"
    STYCS = "STYCS"
    OTHERS = "others"
    DEMO = "DEMO"
    DEMEO = "112o"


class NasStageFolders(StrEnum):
    """Each Folder on the NAS describes a stage in the processing pipeline
    RAW: Raw data from drone flights (e.g. apx, *.hyspex, *.pcap)
    PROCESSING: Intermediate files for reuse in other processes (e.g. rinex or navigation files)
    PROCESSED: Final radiance and reflectance orthomosaics
    """

    RAW = "0_raw"
    PROCESSING = "2_processing"
    PROCESSED = "3_processed"


# Processing Location
LOCAL_PROCESSING_FOLDER = Path("E:/test")  # Path("E:/mjolnir_processing")
# Storage Location on NAS: use link to NAS at Reckenholz (Z:), not cached at Changins (Y:)!
NAS_BASE_PATH = Path(f"Z:/drone/DERIS_TEST/RE/{AvailableTrials.ZOFE.value}/hypSpec")

# Job Settings
NR_OF_FLIGHT_LINES = 4
SELECTED_TRIAL = AvailableTrials.ZOFE
SELECTED_JOBS = ["ZOFE_260423_80", "ZOFE_260522_80_2"]

if __name__ == "__main__":
    print(f"Starting Pipeline for jobs: {SELECTED_JOBS}")

    # Define Steps

    # Step 1: Fetch Raw Data
    #     Some old data folders from 2025 contain already base station data ["rinex"]
    #     --> Exclude to make sure all base station data is freshly fetched by
    #     BasestationScraper and in the same format.
    fetch_raw_data = CopyJobFolders(
        name="Fetch Raw Data",
        input_folder=PipelineFolder(
            basefolder=NAS_BASE_PATH / NasStageFolders.RAW.value,
            target="",
        ),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="RAW"),
        jobs=SELECTED_JOBS,
        exclude_within_output_folder=["rinex"],
    )
    # Step 2: Clean Apx Folder
    #     Move T04 files outside of the flight time range (from flight log) to
    #     apx/removed, so the base station download window is based on the
    #     flight relevant T04 files only.
    clean_apx_files = ApxCleaning(
        name="Clean Apx Files",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="RAW"),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="RAW/apx/removed"
        ),
        jobs=SELECTED_JOBS,
        buffer=timedelta(
            minutes=10
        ),  # 10min before and after data acquisition range to make sure whole mission including calibration is covered
    )
    # Step 3: Download Base Station Data from Swipos
    #     Use the APX files in the raw data to get the flight time info for the scraper
    #     to know which base station data to download.
    download_base_station_data = ScrapeBaseStationData(
        name="Download Base Station Data",
        # Use data from APX folder to get flight time info for scraper
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="RAW/apx"
        ),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="RAW/rinex"
        ),
        jobs=SELECTED_JOBS,
    )

    # Step 4: Store Base Station Data persistent on NAS
    #     Note: Basestation Data are only downloadable for 1 year on the Swipos server, so we save them to NAS for future use.
    store_basestationdata_on_nas = CopyJobFolders(
        name="Store Base Station Data on NAS",
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="RAW/rinex"
        ),
        output_folder=PipelineFolder(
            basefolder=NAS_BASE_PATH / NasStageFolders.PROCESSING.value,
            target="rinex",
        ),
        jobs=SELECTED_JOBS,
        exclude_within_output_folder=["rinex"],
    )

    # Step 5: Georeference Sensors
    georeference_sensors = GeoreferenceSensors(
        name="Georeference Sensors (SWIR, VNIR, LiDAR)",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="RAW"),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="tmp"),
        jobs=SELECTED_JOBS,
    )

    # Step 6: Fetch Navigation Files
    fetch_navigation_files = FetchNavigationFiles(
        name="Fetch Navigation Files",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target=""),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/input_hyspexnav"
        ),
        jobs=SELECTED_JOBS,
    )

    # Step 7: NavigationDiscretization
    navigation_discretization = NavigationDiscretization(
        name="Navigation Discretization",
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/input_hyspexnav"
        ),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/swirvnir_data"
        ),
        jobs=SELECTED_JOBS,
    )

    # Step 8: Convert Binary to Radiance
    binary_to_radiance = BinaryToRadiance(
        name="Binary to Radiance",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="RAW"),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/swirvnir_data"
        ),
        jobs=SELECTED_JOBS,
    )
    # Step 9: Get VNIR Files
    get_vnir_files = MoveFiles(
        name="Get VNIR Files",
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/swirvnir_data"
        ),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="VNIR"),
        jobs=SELECTED_JOBS,
        regex_pattern=r"v1240",  # v1240 for VNIR
    )

    # Step 10: Get SWIR Files
    get_swir_files = MoveFiles(
        name="Get SWIR Files",
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="tmp/swirvnir_data"
        ),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="SWIR"),
        jobs=SELECTED_JOBS,
        regex_pattern=r"s620",  # s620 for VNIR
    )
    # Deprecated (since Intacor release): Build Digital Surface Model (DSM) from LiDAR Point Cloud
    build_digital_surface_model = BuildDigitalSurfaceModel(
        name="Build Digital Surface Model",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target=""),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="output/1_raw/DSM"
        ),
        jobs=SELECTED_JOBS,
    )
    # Step 11: Get SWIR Calibration Files
    #      Note: Required as Parge Preparation
    get_swir_calibration_files = CopyFiles(
        name="Get SWIR Calibration Files",
        input_folder=PipelineFolder(
            basefolder=get_base_path(__file__).parent / "apps",
            target="calibration",
            static=True,
        ),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="SWIR"),
        jobs=SELECTED_JOBS,
        regex_pattern=r"boresight_swir|sensormodel",
    )

    # Step 12: Get VNIR Calibration Files
    #      Note: Required as Parge Preparation
    get_vnir_calibration_files = CopyFiles(
        name="Get VNIR Calibration Files",
        input_folder=PipelineFolder(
            basefolder=get_base_path(__file__).parent / "apps",
            target="calibration",
            static=True,
        ),
        output_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target="VNIR"),
        jobs=SELECTED_JOBS,
        regex_pattern=r"boresight_vnir|sensormodel",
    )
    # Step 13: Geocoding
    geocoding = Geocoding(
        name="Geocoding",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target=""),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="output"
        ),
        jobs=SELECTED_JOBS,
        nr_of_flight_lines=NR_OF_FLIGHT_LINES,
        direct_las_import=True,  # Use direct LAS import instead of DSM
    )
    # Step 14: Create Radiance Orthomosaic
    create_radiance_orthomosaic = CreateRadianceOrthomosaic(
        name="Create Radiance Orthomosaic",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target=""),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="output"
        ),
        jobs=SELECTED_JOBS,
    )
    # Step 15: Create Reflectance Orthomosaic
    create_reflectance_orthomosaic = CreateReflectanceOrthomosaic(
        name="Create Reflectance Orthomosaic",
        input_folder=PipelineFolder(basefolder=LOCAL_PROCESSING_FOLDER, target=""),
        output_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="output"
        ),
        jobs=SELECTED_JOBS,
    )

    # Step 16: Translate Orthomosaics to Geotiff
    orthomosaic_to_geotiff = OrthomosaicToGeoTiff(
        name="Translate Orthomosaics to Geotiff",
        input_folder=PipelineFolder(
            basefolder=LOCAL_PROCESSING_FOLDER, target="output/7_mosaics"
        ),
        output_folder=PipelineFolder(
            basefolder=Path(LOCAL_PROCESSING_FOLDER), target="output/7_mosaics"
        ),
        jobs=SELECTED_JOBS,
    )

    # Run Steps
    # fetch_raw_data.run()
    clean_apx_files.run()
    download_base_station_data.run()
    store_basestationdata_on_nas.run()
    # georeference_sensors.run()

    # fetch_navigation_files.run()
    # navigation_discretization.run()
    # binary_to_radiance.run()
    # get_vnir_files.run()
    # get_swir_files.run()

    # Required for Parge (Georectification)
    # get_swir_calibration_files.run()
    # get_vnir_calibration_files.run()

    # geocoding.run()
    # create_radiance_orthomosaic.run()
    # create_reflectance_orthomosaic.run()
    # orthomosaic_to_geotiff.run()

    print("All Pipeline steps completed.")
