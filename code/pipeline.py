from abc import ABC, abstractmethod

from pathlib import Path

class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""
    jobs : list[str]
    input_basefolder: Path
    output_basefolder: Path

    @abstractmethod
    def execute(self) -> bool:
        """Execute the pipeline step."""
        pass


class PipelineFolder:
    """Defines folder structure for folders used within pipeline jobs."""
    def __init__(self, basefolder: Path, target: str):
        self.basefolder = basefolder
        self.target = target
    
    def get_paths(self, job_names: list[str]) -> list[Path]:
        """Get the full path for a specific job."""
        return [self.basefolder / name / self.target for name in job_names]