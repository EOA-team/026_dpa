from code.pipeline.base import PipelineStep, PipelineFolder
from code.apps.hyspexrad import HyspexRadApplication
from shutil import copytree

class CopyJobFolders(PipelineStep):
    """Copies folder from input to output for each job."""
    def __init__(self, jobs: list[str], input_folder: PipelineFolder, output_folder: PipelineFolder):
        super().__init__(jobs, input_folder, output_folder)

    
    def run(self) -> bool:
        print("Starting to copy job folders...⏳")
        for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            copytree(input_folder, output_folder)
            print(f"Copied {input_folder} to {output_folder}")
        
        print("Copying is finished for ✅")
        return True

class BinaryToRadiance(PipelineStep):
    """Converts binary files to radiance files for each job."""
    def __init__(self, jobs: list[str], input_folder: PipelineFolder, output_folder: PipelineFolder, app_instance= "HyspexRadApplication"):
        super().__init__(jobs, input_folder, output_folder)
        self.app_instance = app_instance

    def run(self) -> bool:
        print("Starting to convert binary files to radiance...⏳")
        hyspexrad = HyspexRadApplication(input_folders=self.input_folders, output_folders=self.output_folders)
        hyspexrad.run()
        print("Converted binary files to radiance.✅")
        return True
    
