import logging
from pathlib import Path
from shutil import copytree, rmtree
from code.file_utils import check_path_exists, check_drive_mounted,copy_with_logging, get_base_path
from code.yamlconfig_helper import  replace_config_placeholder, resolve_relative_paths
from code.scrapers.trajectory_scraper import TrajectoryScraper

logger = logging.getLogger(__name__)

def hd_to_nas_transfer(config: dict) -> None:
    logger.info("Starting Hard Drive to NAS Transfer")
    #Abort if NAS not mounted
    check_drive_mounted(
        path=Path(config['file_transfer']['hd_to_nas']['destination_path']))
    #Get Flight Folder
    flight_folder = get_flight_folder(
        recordings_path= Path(config['file_transfer']['hd_to_nas']['source_path']).parent)
    #Load Resolve Config
    resolved_config =get_resolved_config(
        config=config, 
        flight_folder=flight_folder)
    #Processing Steps
    scrape_trajectory_data(config=resolved_config)
    transfer_recordings_data(config=resolved_config)