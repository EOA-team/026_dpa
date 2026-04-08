""" In the future there will be many different runner scripts for different pipelines
At The moment at Agroscope we only use one default pipeline but in Future ther
will probably be different
Example:
 default_pipeline_runner.py
 high_accuracy_pipeline_runner.py # using georeferencing and additional corrections
 fast_processing_pipeline_runner.py # using only essential steps for fast processing
 etc.
"""

from code.pipeline.steps import CopyJobFolders, BinaryToRadiance, MoveFiles, EstimateTrajectory, ScrapeBaseStationData
from code.pipeline.base import PipelineFolder, Path

if __name__ == "__main__":
    selected_jobs = ["re112o_250610", "re112o_250619","re112o_250717_2","re112o_250723_4",
                     "re112o_250807", "re112o_250813", "re112o_250903", "re112o_250918"]
    print(f"Starting Pipeline for jobs: {selected_jobs}")

    # Define Steps
    fetch_raw_data = CopyJobFolders(name="Fetch Raw Data",
                                    input_folder=PipelineFolder(
                                        Path("D:/data/mjolnir"), "01_raw_data"),
                                    output_folder=PipelineFolder(
                                        Path("E:/mjolnir_processing"), "RAW"),
                                    jobs=selected_jobs,
                                    exclude_within_output_folder=["rinex"]) # Some folders already contain base station data (Make sure there is no duplicate or wrong format)
    download_base_station_data = ScrapeBaseStationData(name="Download Base Station Data",
                                    input_folder=PipelineFolder(
                                        Path("E:/mjolnir_processing"), "RAW/apx"), #Use data from APX folder to get flight time info for scraper
                                    output_folder=PipelineFolder(
                                        Path("E:/mjolnir_processing"), "RAW/rinex"),
                                    jobs = selected_jobs)
    

    binary_to_radiance = BinaryToRadiance(name="Binary to Radiance",
                                          input_folder=PipelineFolder(
                                              Path("E:/mjolnir_processing"), "RAW"),
                                          output_folder=PipelineFolder(
                                              Path("E:/mjolnir_processing"), "tmp"),
                                          jobs=selected_jobs)

    get_vnir_files = MoveFiles(name="Get VNIR Files",
                               input_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "tmp"),
                               output_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "VNIR"),
                               jobs=selected_jobs,
                               regex_pattern=r"v1240")  # v1240 for VNIR

    get_swir_files = MoveFiles(name="Get SWIR Files",
                               input_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "tmp"),
                               output_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "SWIR"),
                               jobs=selected_jobs,
                               regex_pattern=r"s620")  # s620 for VNIR
    
    estimate_trajectory = EstimateTrajectory(name="Estimate Trajectory",
                               input_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "RAW"),
                               output_folder=PipelineFolder(
                                   Path("E:/mjolnir_processing"), "tmp"),
                               jobs=selected_jobs)  

    # Run Steps
    fetch_raw_data.run()
    download_base_station_data.run()
    binary_to_radiance.run()
    get_vnir_files.run()
    get_swir_files.run()
    estimate_trajectory.run()

    print("All Pipeline steps completed.")
