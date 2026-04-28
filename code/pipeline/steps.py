"""
Defines various pipeline steps.
A pipeline step implements a `run` method, which can take one of the following forms:
1. **Direct Python instructions** 
for simple tasks such as copying or moving files.
2. **Calls to a more complex Python class** 
for advanced operations, e.g., automatic georeferencing of orthomosaics using GDAL.
3. **Calls to a Windows application** 
for steps that cannot yet be implemented in Python and must be simulated.
"""
from shutil import copytree
from shutil import ignore_patterns, copy2
from pathlib import Path
from datetime import timedelta


from code.pipeline.base import PipelineStep, PipelineFolder
from code.apps.hyspexrad import HyspexRadApplication
from code.apps.pospacuav import PosPacUavApplication
from code.apps.hyspexnav import HyspexNavApplication
from code.scrapers.basestation_scraper import RinexDownloadWindow, BasestationScraper
from code.filehandling_helper import move_files_by_regex, copy_files_by_regex
from code.scrapers.base_scraper import BaseScraper
from code.file_utils import move_and_extract_downloaded_zip, find_las_file
from code.pdalgdal_helpers import las_to_geotif, geotiff_to_envi_dsm, fix_envi_header

from dotenv import load_dotenv

# Pylint Note :
# Pipeline steps are known to have at most 6 arguments, exceeding pylint's default limit of 5.
# This is intentional: each step requires folders, job names, and configuration parameters.
# Similarly, exposing only a single public run() method is by design —
# a pipeline step has one responsibility: to be run.

# pylint: disable=too-many-arguments, too-few-public-methods, too-many-positional-arguments

class CopyJobFolders(PipelineStep):
    """Copies data folders from input to output for each job.

    Excludes specified subfolders to avoid copying data that is either already
    processed or should be freshly fetched by a dedicated pipeline step.

    Args:
        exclude_within_output_folder: List of subfolder names to skip during copy.
            Some job folders contain pre-processed data from previous manual workflows
            that should not be reused (e.g. 'rinex' folders should always be freshly
            fetched by the ScrapeBaseStationData step to ensure consistent format).
    """

    def __init__(self, name: str, jobs: list[str], input_folder: PipelineFolder,
                 output_folder: PipelineFolder,
                 exclude_within_output_folder: list[str] | None = None):
        super().__init__(name, jobs, input_folder, output_folder)
        self.exclude_within_output_folder = exclude_within_output_folder

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            ignore_ptrn = ignore_patterns(
                *self.exclude_within_output_folder) if self.exclude_within_output_folder else None
            copytree(input_folder, output_folder, ignore=ignore_ptrn)
            print(f"Copied {input_folder} to {output_folder}")

        print(f"Finished Step: {self.name} ✅")
        return True


class ScrapeBaseStationData(PipelineStep):
    """Scrapes base station data from Swipos for each job and saves it to the output folder."""

    def run(self) -> bool:
        load_dotenv()  # Load environment variables from .env file
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            obs = RinexDownloadWindow(
                apx_folder=input_folder,
                convergence_time=timedelta(minutes=60), # Add RTX convergence time
                end_buffer=timedelta(minutes=15)
            )

            config_dict = {
                "browser": "firefox",
                "driver_path": "C:/Tools/webdrivers/geckodriver.exe",
                "timeout": 5,
                "destination_path": output_folder,
                "service_url": "https://shop.swipos.ch/",
                "username": BaseScraper.load_environment_variable("SWIPOS_USER"),
                "password": BaseScraper.load_environment_variable("SWIPOS_PW"),
            }

            print(f"Scraping base station data for {input_folder}...")
            scraper = BasestationScraper(
                config=config_dict, observation_time=obs)
            scraper.run()
            move_and_extract_downloaded_zip(output_folder)

        print(f"Finished Step: {self.name} ✅")
        return True


class MoveFiles(PipelineStep):
    """Moves specified files from input to output for each job."""

    def __init__(self, name: str, jobs: list[str], input_folder: PipelineFolder,
                 output_folder: PipelineFolder, regex_pattern: str):
        super().__init__(name, jobs, input_folder, output_folder)
        self.regex_pattern = regex_pattern

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            move_files_by_regex(
                input_folder, output_folder, self.regex_pattern)
        print(f"Finished Step: {self.name} ✅")
        return True


class CopyFiles(PipelineStep):
    """Copies specified files from input to output for each job."""

    def __init__(self, name: str, jobs: list[str], input_folder: PipelineFolder,
                 output_folder: PipelineFolder, regex_pattern: str):
        super().__init__(name, jobs, input_folder, output_folder)
        self.regex_pattern = regex_pattern

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            copy_files_by_regex(
                input_folder, output_folder, self.regex_pattern)
        print(f"Finished Step: {self.name} ✅")
        return True


class BinaryToRadiance(PipelineStep):
    """Converts binary files to radiance files for each job."""

    def __init__(self, name: str, jobs: list[str], input_folder: PipelineFolder,
                 output_folder: PipelineFolder, app_instance="HyspexRadApplication"):
        super().__init__(name, jobs, input_folder, output_folder)
        self.app_instance = app_instance

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        hyspexrad = HyspexRadApplication(
            input_folders=self.input_folders, output_folders=self.output_folders)
        hyspexrad.run()
        print(f"Finished Step: {self.name} ✅")
        return True


class GeoreferenceSensors(PipelineStep):
    """
    Runs the full POSPac UAV processing pipeline for each job.
    - Creates a post-processed trajectory (SBET) using ETH2 base station (INFusion Single Base).
    - Georeferences the VNIR and SWIR sensors using the generated SBET.
    - Generates a georeferenced LAS point cloud from raw LiDAR data.
    """

    def __init__(self, name: str, jobs: list[str], input_folder: PipelineFolder,
                 output_folder: PipelineFolder, app_instance="PosPacUavApplication"):
        super().__init__(name, jobs, input_folder, output_folder)
        self.app_instance = app_instance

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        pospacuav = PosPacUavApplication(
            input_folders=self.input_folders, output_folders=self.output_folders)
        pospacuav.run()
        print(f"Finished Step: {self.name} ✅")
        return True


class FetchNavigationFiles(PipelineStep):
    """Fetches all input files required by HySpex NAV into the navigation files folder.

    Copies the following files for each job:
        - events.txt              trigger timestamps per scan line
        - VNIR_all_records.txt    continuous IMU data for VNIR sensor
        - SWIR_all_records.txt    continuous IMU data for SWIR sensor
        - {job_name}.log          flight line start/stop times and bands

    The first three files are copied from a known path, e.g.:
        tmp/re112o_250717_full_processing/Mission 1/Export/events.txt
        tmp/re112o_250717_full_processing/Mission 1/Export/VNIR_all_records.txt
        tmp/re112o_250717_full_processing/Mission 1/Export/SWIR_all_records.txt

    The log file is matched by regex (*.log) since its name varies per job —
    it may include a flight height suffix or not, e.g.:
        re112o_250717.log
        re112o_250717_80m2.log
    """

    def copy_known_file_paths(self, input_folder: Path, output_folder: Path) -> None:
        """Copy files from known paths to the output folder."""
        events_file = input_folder / "tmp" / \
            f"{input_folder.name}_full_processing" / \
            "Mission 1" / "Export" / "events.txt"
        swir_records_file = input_folder / "tmp" / \
            f"{input_folder.name}_full_processing" / \
            "Mission 1" / "Export" / "SWIR_all_records.txt"
        vnir_records_file = input_folder / "tmp" / \
            f"{input_folder.name}_full_processing" / \
            "Mission 1" / "Export" / "VNIR_all_records.txt"
        for file in [events_file, swir_records_file, vnir_records_file]:
            if file.exists():
                copy2(file, output_folder / file.name)
            else:
                print(f"⚠️ Warning: Expected file not found: {file}")

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            # ensure output folder exists
            output_folder.mkdir(parents=True, exist_ok=True)
            self.copy_known_file_paths(input_folder, output_folder)
            # For the log file the name can vary--> use regex to find it
            copy_files_by_regex(
                source=input_folder / "RAW",
                destination=output_folder,
                regex_pattern=r".*\.log"
            )

        print(f"Finished Step: {self.name} ✅")
        return True


class NavigationDiscretization(PipelineStep):
    """Runs the HySpex NAV application to discretize navigation files for each job."""

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        hyspexnav = HyspexNavApplication(
            input_folders=self.input_folders, output_folders=self.output_folders)
        hyspexnav.run()
        print(f"Finished Step: {self.name} ✅")
        return True


class BuildDigitalSurfaceModel(PipelineStep):
    """Creates a digital surface model from the las point cloud file."""

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            las_file_path = find_las_file(input_folder)
            las_to_geotif(
                input_las=las_file_path,
                output_tif=output_folder / "DSM.tif",
                resolution=0.05
            )

            geotiff_to_envi_dsm(
                input_tif=output_folder / "DSM.tif",
                output_file=output_folder / "DSM"
            )

            fix_envi_header(output_folder / "DSM.hdr")

        print(f"Finished Step: {self.name} ✅")
        return True
