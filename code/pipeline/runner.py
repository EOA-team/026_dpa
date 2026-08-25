""" In the future there will be many different runner scripts for different pipelines
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
    ScrapeBaseStationData,
    OrthomosaicToGeoTiff,
)

NR_OF_FLIGHT_LINES = 5

if __name__ == "__main__":
    selected_jobs = ["ZOFE_260522_80_5"]
  
    print(f"Starting Pipeline for jobs: {selected_jobs}")

    # Define Steps

    # Step 1: Fetch Raw Data
    #     Some old data folders from 2025 contain already base station data ["rinex"]
    #     --> Exclude to make sure all base station data is freshly fetched by
    #     BasestationScraper and in the same format.
    fetch_raw_data = CopyJobFolders(
        name="Fetch Raw Data",
        input_folder=PipelineFolder(
            basefolder=Path("Z:/drone/DERIS/data/RE/ZOFE/hypSpec"), # Important: use link to NAS at Reckenholz, not cached at Changins!
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW"),
        jobs=selected_jobs,
        exclude_within_output_folder=["rinex"]
    )
    # Step 2: Download Base Station Data from Swipos
    #     Use the APX files in the raw data to get the flight time info for the scraper
    #     to know which base station data to download.
    download_base_station_data = ScrapeBaseStationData(
        name="Download Base Station Data",
        # Use data from APX folder to get flight time info for scraper
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW/apx"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW/rinex"),
        jobs=selected_jobs
    )
    #Step 3: Georeference Sensors
    georeference_sensors = GeoreferenceSensors(
        name="Georeference Sensors (SWIR, VNIR, LiDAR)",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp"),
        jobs=selected_jobs)

    #Step 4: Fetch Navigation Files
    fetch_navigation_files = FetchNavigationFiles(
        name="Fetch Navigation Files",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/input_hyspexnav"),
        jobs=selected_jobs)

    #Step 5: NavigationDiscretization
    navigation_discretization = NavigationDiscretization(
        name="Navigation Discretization",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/input_hyspexnav"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/swirvnir_data"),
        jobs=selected_jobs
    )

    #Step 6: Convert Binary to Radiance
    binary_to_radiance = BinaryToRadiance(
        name="Binary to Radiance",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/swirvnir_data"),
        jobs=selected_jobs
    )
    #Step 7: Get VNIR Files
    get_vnir_files = MoveFiles(
        name="Get VNIR Files",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/swirvnir_data"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="VNIR"),
        jobs=selected_jobs,
        regex_pattern=r"v1240"  # v1240 for VNIR
    )

    #Step 8: Get SWIR Files
    get_swir_files = MoveFiles(
        name="Get SWIR Files",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="tmp/swirvnir_data"),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="SWIR"),
        jobs=selected_jobs,
        regex_pattern=r"s620"  # s620 for VNIR
    )
    #Step 9: Build Digital Surface Model (DSM) from LiDAR Point Cloud
    build_digital_surface_model = BuildDigitalSurfaceModel(
        name="Build Digital Surface Model",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="DSM"),
        jobs=selected_jobs
    )
    # Step 10: Get SWIR Calibration Files
    #      Note: Required as Parge Preparation
    get_swir_calibration_files = CopyFiles(
        name="Get SWIR Calibration Files",
        input_folder=PipelineFolder(
            basefolder=get_base_path(__file__).parent / "apps",
            target="calibration", static=True),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="SWIR"),
        jobs=selected_jobs,
        regex_pattern=r"boresight_swir|sensormodel")

    # Step 11: Get VNIR Calibration Files
    #      Note: Required as Parge Preparation
    get_vnir_calibration_files = CopyFiles(
        name="Get VNIR Calibration Files",
        input_folder=PipelineFolder(
            basefolder=get_base_path(__file__).parent / "apps",
            target="calibration",
            static=True),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="VNIR"),
        jobs=selected_jobs,
        regex_pattern=r"boresight_vnir|sensormodel"
    )
    # Step 12: Geocoding
    geocoding =  Geocoding(
        name="Geocoding",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="output"),
        jobs=selected_jobs,
        nr_of_flight_lines = NR_OF_FLIGHT_LINES
    )
    # Step 13: Create Radiance Orthomosaic
    create_radiance_orthomosaic = CreateRadianceOrthomosaic(
        name="Create Radiance Orthomosaic",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="output"),
        jobs=selected_jobs
    )
    # Step 14: Create Reflectance Orthomosaic
    create_reflectance_orthomosaic = CreateReflectanceOrthomosaic(
        name="Create Reflectance Orthomosaic",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="output"),
        jobs=selected_jobs
    )

    # Step 15: Translate Orthomosaics to Geotiff 
    orthomosaic_to_geotiff = OrthomosaicToGeoTiff(
        name="Translate Orthomosaics to Geotiff",
        input_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="output/mosaics"),
        output_folder=PipelineFolder(
            basefolder=Path(Path("E:/mjolnir_processing")),
            target="output/mosaics"),
        jobs=selected_jobs
    )


    # Run Steps
    fetch_raw_data.run()
    download_base_station_data.run()
    georeference_sensors.run()

    fetch_navigation_files.run()
    navigation_discretization.run()
    binary_to_radiance.run()
    get_vnir_files.run()
    get_swir_files.run()

    build_digital_surface_model.run()

    # Required for Parge (Georectification)
    get_swir_calibration_files.run()
    get_vnir_calibration_files.run()

    geocoding.run()
    create_radiance_orthomosaic.run()   
    create_reflectance_orthomosaic.run()
    orthomosaic_to_geotiff.run()
    

    print("All Pipeline steps completed.")
