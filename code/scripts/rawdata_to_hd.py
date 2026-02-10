""" Just a quick script to move data from DAU to HD
"""

from code.pipeline.steps import CopyJobFolders, BinaryToRadiance, MoveFiles
from code.pipeline.base import PipelineFolder, Path

if __name__ == "__main__":
    selected_jobs = ["re112o_250807_80m4", "re112o_250918_80m" ]
    print(f"Starting Pipeline for jobs: {selected_jobs}")
    # Define Steps
    fetch_raw_data = CopyJobFolders(name="Fetch Raw Data",
                                    input_folder=PipelineFolder(
                                        Path("D:/HySpexAir/Recordings"), target=""),
                                    output_folder=PipelineFolder(
                                        Path("E:/test_fetch_dua2"), target=""),
                                    jobs=selected_jobs)
    fetch_raw_data.run()


    print("All Pipeline steps completed.")
