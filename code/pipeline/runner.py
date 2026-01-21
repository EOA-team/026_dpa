from code.pipeline.steps import CopyJobFolders, BinaryToRadiance
from code.pipeline.base import PipelineFolder, Path

if __name__ == "__main__":
    selected_jobs = ["re112o_250610", "re112o_250918"]
    print(f"Starting Pipeline for jobs: {selected_jobs}")

    # Define Steps
    fetch_raw_data = CopyJobFolders(input_folder=PipelineFolder(Path("D:/data/mjolnir"), "01_raw_data"),
                                    output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "RAW"),
                                    jobs=selected_jobs)
    
    binary_to_radiance = BinaryToRadiance(input_folder=PipelineFolder(Path("E:/mjolnir_processing"), "RAW"),
                                          output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "tmp"),
                                          jobs=selected_jobs)

    # Run Steps
    fetch_raw_data.run()
    binary_to_radiance.run()

    print("All Pipeline steps completed.")


    
    