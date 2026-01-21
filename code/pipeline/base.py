from abc import ABC, abstractmethod
from pathlib import Path

class PipelineFolder:
    """A pipeline folder represents a base folder and a target subfolder.
    Combinded with a specific job this results  in e.g. basefolder/job_name/target

    The target is a subfolder name under each job folder and hold specific data for that step.

    Example: 
        basefolder: D:/data/mjolnir
        target: 01_raw_data
        job_name: ["re112o_250610", "re112o_250918"]
        -->[D:/data/mjolnir/re112o_250610/01_raw_data, D:/data/mjolnir/re112o_250918/01_raw_data]"""
    
    def __init__(self, basefolder: Path, target: str):
        self.basefolder = basefolder
        self.target = target
    
    def get_paths(self, job_names: list[str]) -> list[Path]:
        """Get the full path for a specific job."""
        return [self.basefolder / name / self.target for name in job_names]

class PipelineStep(ABC):
    """Base class for pipeline steps."""
    def __init__(self, jobs: list[str], input_folder: PipelineFolder, output_folder: PipelineFolder):
        self.jobs = jobs
        self.input_folders = input_folder.get_paths(jobs)
        self.output_folders = output_folder.get_paths(jobs)
    
    @abstractmethod
    def run(self) -> bool:
        """Run the pipeline step. Must be implemented by subclasses."""
        pass

    def get_paths(self) -> list[Path]:
        """Get the full path for a specific job."""
        return [self.input_folder / self.jobs / self.target for job in self.jobs]

