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

from code.pipeline.base import PipelineStep, PipelineFolder
from code.apps.hyspexrad import HyspexRadApplication
from code.apps.pospacuav import PosPacUavApplication
from code.scrapers.basestation_scraper import TrajectoryObservationTimeFetcher
from code.filehandling_helper import move_files_by_regex

from shutil import copytree


class CopyJobFolders(PipelineStep):
    """Copies folder from input to output for each job."""

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            copytree(input_folder, output_folder)
            print(f"Copied {input_folder} to {output_folder}")

        print(f"Finished Step: {self.name} ✅")
        return True
    
class ScrapeBaseStationData(PipelineStep):
    """Scrapes base station data from Swipos for each job and saves it to the output folder."""

    def run(self) -> bool:
        print(f"Starting Step: {self.name} ⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            print(output_folder)
            obs = TrajectoryObservationTimeFetcher(apx_folder=input_folder)
            print(f"Flight start:  {obs.flight_start}")
            print(f"Flight end:    {obs.flight_end}")
            print(f"Duration:      {obs.duration_hours:02d}h {obs.duration_minutes:02d}min")
            print(f"Date:          {obs.date}")
            print(f"Start time:    {obs.start_hour:02d}:{obs.start_minute:02d}:{obs.start_second:02d}")

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