# Drone Pipeline Automation

[![Python](https://img.shields.io/badge/python-3.12-blue)](.python-version)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-blue)](LICENSE)


## What is it?

**dpa** is a data pipeline that allows for a fully automatic data processing of uav hyperspectral imagery. It replaces an internal labour intensive and error-prone manual processing workflow including 6x different proprietary software tools, 2x services and more than 100 parameters that need to be set per uav flight. 

**Please Note!!!** : dpa is not yet released. In dev-branch there is a beta version available (not yet stable)!

- **Why UI Automation and no API?** :  UI Automation is definetely less reliable but current licensing cost forces us to stay with UI-based software. To increase reliability of Pipeline we tried to reduce UI-Interactions to a minimum (e.g using PospacUAV Batch-Manager, XML Files)

- **Can I run this pipeline on my computer?** :  No currently this pipeline only runs on a dedicated server (windows 11) with dedicated software versions installed. Step by Step the UI Automation should be replaced with API so that in future this pipeline can run on any linux server (docker).

<p align="center">
<img width="620" height="402" alt="image" src="https://github.com/user-attachments/assets/44932fd7-6e19-40d8-8f25-2aface7dbf56" />
</p>

## Dependencies , Services, Software
- major packages: [pywinauto](https://github.com/pywinauto/pywinauto), [gdal](https://github.com/osgeo/GDAL), [pdal](https://github.com/PDAL/PDAL), [numpy](https://github.com/numpy/numpy), [pandas](https://github.com/pandas-dev/pandas)
- services: [swipos](https://www.swisstopo.admin.ch/de/swipos-der-swiss-positioning-service), apx20 webservice
- software: [pospac uav 9.3](https://applanix.trimble.com/en/software/applanix-pospac-uav-complete), [hyspxrad v3.5](https://www.hyspex.com/), [hyspexnav v2.6.1](https://www.hyspex.com/), [intacor](https://intacor.com/),
  [parge](https://www.rese-apps.com/parge/), [droacor](https://droacor.com/)
  

## Main Features
- **Data Preparation**: File Handling and Folder Structure (copy, move, regex, ...)
- **Modular Architecture**: Each Pipeline-Step can be replaced with new SW-Versions, different SW-Tools or even internal developed python algorithms.
- **Configurable Runner Scripts**: Processes and Data Structure changes fast in Research. Our researchers need a simple script (high abstraction) to adjust the pipeline to their specific needs without understanding every detail of the code.
- **Batch Processing**: Process batches of flights within one go (Speed-Up)
- **Data Scraping** : Swiss Positioning Service Swipos
- **End-to-End Pipeline** including all pipeline steps from raw hyperspectral imagery to final radinace and reflectance orthomosaics.

## Current State

All Issues can be found here : https://github.com/EOA-team/026_dpa/issues

### Bugs
- **UI Automation instable in Multi-Monitor-Mode** : Sometimes pywinauto fails to detect auto_ids in PospacUAV
- **UI Automation does not work in background**: UI needs to be in foreground all the time (no Screensaver or minimizing of window!)
- **UI Automation instable** : Now and then pipeline fails because it cannot find a UI Control (temporary solve: restart drone station)

Note: If your batch process fails midway , have a look at the processing log and see at which pipelinestep the process failed. Simply uncomment the run-functions in runner.py which were already successfull and restart process. 

### Features and Updates (Coming soon)
- **Integration of INTACOR (replace M4MProc)** : 
   - Bug Fixes: Removal of Peak Reflectance at 940nm and 2000nm
   - New Feature : DSM Import from las, ...
- **Removal of Convergence Time Padding**: Results in processing speed-up
- **Update to PospacUAV 9.4**
- **Update to IDL 91**
- **Direct Georeferencing**: Increases accuracy from 2-10cm to ~2-3cm
- **Space Saver**: Remove intermediate results and only save logs for data lineage
- **All open Issues can be found here**: 

## How to use it?

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
