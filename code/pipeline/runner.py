from code.pipeline.steps import CopyJobFolders, BinaryToRadiance, MoveFiles
from code.pipeline.base import PipelineFolder, Path

if __name__ == "__main__":
    selected_jobs = ["re112o_250610", "re112o_250918"]
    print(f"Starting Pipeline for jobs: {selected_jobs}")

    # Define Steps
    fetch_raw_data = CopyJobFolders(name="Fetch Raw Data", 
                                    input_folder=PipelineFolder(Path("D:/data/mjolnir"), "01_raw_data"),
                                    output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "RAW"),
                                    jobs=selected_jobs)
    
    binary_to_radiance = BinaryToRadiance(name="Binary to Radiance",
                                          input_folder=PipelineFolder(Path("E:/mjolnir_processing"), "RAW"),
                                          output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "tmp"),
                                          jobs=selected_jobs)
    
    get_vnir_files = MoveFiles( name="Get VNIR Files",
                                input_folder=PipelineFolder(Path("E:/mjolnir_processing"), "tmp"),
                                output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "VNIR"),
                                jobs=selected_jobs,
                                regex_pattern=r"v1240") # v1240 for VNIR
    
    get_swir_files = MoveFiles( name="Get SWIR Files",
                                input_folder=PipelineFolder(Path("E:/mjolnir_processing"), "tmp"),
                                output_folder=PipelineFolder(Path("E:/mjolnir_processing"), "SWIR"),
                                jobs=selected_jobs,
                                regex_pattern=r"s620") # s620 for VNIR
    


    # Run Steps
    #fetch_raw_data.run()
    #binary_to_radiance.run()
    get_vnir_files.run()
    get_swir_files.run()


    print("All Pipeline steps completed.")


    
    