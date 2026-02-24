import logging
from pathlib import Path
from shutil import copytree, rmtree
from code.file_utils import  check_drive_mounted,copy_with_logging
from code.tools.postflightdtt.postflightdtt_helpers import get_flight_folder, get_resolved_config


logger = logging.getLogger(__name__)

def hd_to_nas_transfer(config: dict) -> None:
    logger.info("Starting Hard Drive to NAS Transfer")
    #Abort if NAS not mounted
    check_drive_mounted(
        path=Path(config['file_transfer']['hd_to_nas']['destination_path']))
    #Load Resolve Config
    resolved_config =get_resolved_config(config=config)
    #Processing Steps
    transfer_harddisk_data(config=resolved_config)

def transfer_harddisk_data(config) -> None:
    source_path = config['file_transfer']['hd_to_nas']['source_path']
    destination_path = config['file_transfer']['hd_to_nas']['destination_path']
    # Backup before transfer if enabled in config
    backup = config['file_transfer']['hd_to_nas']['backup']
    if backup:
        logger.info("Backup enabled - backing up source before transfer")
        backup_path = config['file_transfer']['hd_to_nas']['backup_path']
        copytree(src=source_path, # backup the entire recordings folder
                 dst=backup_path, 
                 dirs_exist_ok=True,  # Allow overwriting existing data
                 copy_function=copy_with_logging
                 )
        logger.info("Backed up %s to %s", source_path, backup_path)
    #Transfer data
    logger.info("Transferring Hard Disk data to NAS...")
    copytree(src=source_path, # backup the entire recordings folder
             dst=destination_path, 
             dirs_exist_ok=True, # Allow overwriting existing data
             copy_function=copy_with_logging
            )
    logger.info("Copied %s to %s", source_path, destination_path)
    #Cleanup
    rmtree(source_path)
    source_path.mkdir() # Recreate empty recordings folder after transfer
    logger.info("Deleted all files in %s", source_path.parent)