""" In this module the base classes needed to build a pipeline are defined:
1. A PipelineFolder : 
Defines either a input or output folder for a specific step in the pipeline.
2. A PipelineStep : 
Defines a processing step in the pipeline, handling input and output folders for each job.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class PipelineFolder:
    """Represents a folder location in the processing pipeline.

    Dynamic (default):
        Combined with a job name, resolves to basefolder / job_name / target.
        Each job gets its own subfolder.

        Example:
        basefolder : D:/data/mjolnir
        target     : 01_raw_data
        jobs       : ["re112o_250610", "re112o_250918"]
        result     : [D:/data/mjolnir/re112o_250610/01_raw_data,
                      D:/data/mjolnir/re112o_250918/01_raw_data]
    Static:
        The same path is returned for all jobs, regardless of job name.
        Useful for shared resources such as calibration files.

        Example:
        basefolder : get_base_path(__file__).parent
        target     : calibration
        jobs       : ["re112o_250610", "re112o_250918"]
        result     : [get_base_path(__file__).parent / calibration,
                      get_base_path(__file__).parent / calibration]
 
    """

    def __init__(self, basefolder: Path, target: str, static: bool = False):
        self.basefolder = basefolder
        self.target = target
        self.static = static # If static is true, the folder is not job specific and the same for all jobs (e.g. calibration files)
    def get_job_paths(self, job_names: list[str]) -> list[Path]:
        """Resolve folder paths for the given jobs.
        Dynamic: one path per job as basefolder / job_name / target.
        Static:  one shared path as basefolder / target, repeated for all jobs.
        """
        if self.static:
             return [self.basefolder / self.target] * len(job_names)
        return [self.basefolder / name / self.target for name in job_names]



class PipelineStep(ABC):
    """Base class for pipeline steps.
    Already generates input and output folder paths for each job during initialization
    Subclasses must implement the run method.
    """
    def __init__(self, name: str, jobs: list[str],
                 input_folder: PipelineFolder, output_folder: PipelineFolder):
        self.name = name
        self.jobs = jobs
        self.input_folders = input_folder.get_job_paths(jobs)
        self.output_folders = output_folder.get_job_paths(jobs)
    @abstractmethod
    def run(self) -> bool:
        """Run the pipeline step. Must be implemented by subclasses."""
