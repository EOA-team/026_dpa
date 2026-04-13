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
from dotenv import load_dotenv
from shutil import ignore_patterns

from code.pipeline.base import PipelineStep, PipelineFolder
from code.apps.hyspexrad import HyspexRadApplication
from code.apps.pospacuav import PosPacUavApplication
from code.scrapers.basestation_scraper import TrajectoryObservationTimeFetcher, BasestationScraper
from code.filehandling_helper import move_files_by_regex
from code.scrapers.base_scraper import BaseScraper
from code.file_utils import move_and_extract_downloaded_zip




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
                 output_folder: PipelineFolder, exclude_within_output_folder: list[str]|None = None):
        super().__init__(name, jobs, input_folder, output_folder)
        self.exclude_within_output_folder = exclude_within_output_folder

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            ignore_ptrn = ignore_patterns(*self.exclude_within_output_folder) if self.exclude_within_output_folder else None
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
            obs = TrajectoryObservationTimeFetcher(apx_folder=input_folder)

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
            scraper = BasestationScraper(config=config_dict, observation_time=obs)
            scraper.run()
            move_and_extract_downloaded_zip(output_folder)


        print(f"Finished Step: {self.name} ✅")
        return True


class MoveFiles(PipelineStep):
    """Copies specified files from input to output for each job."""

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

class EstimateTrajectory(PipelineStep):
    """Estimates flight trajectory from raw GNSS/IMU data for each job."""

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