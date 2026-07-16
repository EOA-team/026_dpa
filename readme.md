# Drone Pipeline Automation

[![Python](https://img.shields.io/badge/python-3.12-blue)](.python-version)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-blue)](LICENSE)


## What is it?

dpa is a data pipeline that allows for a fully automatic data processing of uav hyperspectral imagery. It replaces an internal labour intensive and error-prone manual processing workflow including 6x differen proprietary software tools, 2x services and more than 100 parameters that need to be set per uav flight. 

--- 

## Main Features

- **Data Preparation**: File Handling and Folder Structure (copy, move, regex, ...)
- **Modular Architecture**: Each Pipeline-Step can be replaced with new SW-Versions, different SW-Tools or even internal developed python algorithms.
- **Configurable Runner Scripts**: Processes and Data Structure changes fast in Research. Our researchers need a simple script (high abstraction) to adjust the pipeline to their specific needs without understanding every detail of the code.
- **Batch Processing**: Process batches of flights within one go (Speed-Up)
- **End-to-End Pipeline** including all pipeline steps from raw hyperspectral imagery to final radinace and reflectance orthomosaics.
--- 
## How to use it?**

**1. Make sure you are logged in to the drone station**

**2. Clone repo and swith to dev branch (Beta Version)**
```
git clone git@github.com:EOA-team/026_dpa.git
git switch dev
```
**3. Create Conda Env**
```
conda env create -f environment.yml
```
**4. Adjust the runner.py file :**
- Note: Recommended to run batches of flight campaigns 
- Select Jobs that should be processed 
  ```
  NR_OF_FLIGHT_LINES = 5
  ...
  selected_jobs = ["FLIGHT_260529", "FLIGHT_260529", ""]
  ```
**5. Select desired input and ouput folders**

Note: Normally only adjust input_folder of First Pipeline Step "Fetch Raw Data"
  
```
 fetch_raw_data = CopyJobFolders(
        name="Fetch Raw Data",
        input_folder=PipelineFolder(
            basefolder=Path("Z:/drone/DERIS/data/RE/CampaignXYZ/hypSpec"), 
            target=""),
        output_folder=PipelineFolder(
            basefolder=Path("E:/mjolnir_processing"),
            target="RAW"),
        jobs=selected_jobs,
        exclude_within_output_folder=["rinex"]
    )
```
**6. Run Pipeline**
```
python -m code.pipeline.runner
```


- Base Station Scraper (Swiss Positioning Service Swipos))
- Georeferecing (VNIR,SWIR, LAS) using PospacUAV with Batch Manager 
- Navigation Discretization: Discretizes a continuous IMU/GPS stream against sensor trigger events
- Build DSM: Creates a digital surface model from the las point cloud file
- Geocoding: Attaching a geographic coordinate system to the imagery
- Orthomosaic Creation: Radiance and Reflectance 

team.atlassian.net/wiki/spaces/EOAintern/pages/686359066/026_Rolling_Documentation#Intermediate-Process-Documentation)



