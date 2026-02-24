from shutil import copytree, rmtree, copy2
import sys
from pathlib import Path
import logging
from code.yamlconfig_helper import load_config_from_yamlfile, resolve_relative_paths,replace_config_placeholder
from code.scrapers.trajectory_scraper import TrajectoryScraper
from code.tools.postflightdtt.drone_to_hd import drone_to_hd_transfer

logger = logging.getLogger(__name__)


        
def get_source_path(config: dict, filetransfer: str) -> Path:
    file_transfer_dict = config['file_transfer'][filetransfer]
    _source_path = Path(file_transfer_dict['source_path'])
    return _source_path

def get_destination_path(config: dict, filetransfer: str) -> Path:
    file_transfer_dict = config['file_transfer'][filetransfer]
    _destination_path = Path(file_transfer_dict['destination_path'])
    return _destination_path

def get_delete_after_transfer(config: dict, filetransfer: str) -> bool:
    file_transfer_dict = config['file_transfer'][filetransfer]
    delete_after_transfer = file_transfer_dict['delete_after_transfer'] #should be bool type
    return delete_after_transfer








def clear_folder(folder_path: Path | str) -> None:
    """Remove all contents and recreate the empty folder."""
    folder_path = Path(folder_path)
    rmtree(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)

def copy_with_logging(src, dst):
    """Copy function with size info."""
    size = Path(src).stat().st_size / (1024 * 1024)  # MB
    logger.info("Copying %s (%.2f MB)", Path(src).name, size)
    return copy2(src, dst)

def get_base_path() -> Path:
    """Get base path - works for both script and executable."""
    if getattr(sys, 'frozen', False):
        # Running as executable (PyInstaller)
        base_path = Path(sys.executable).parent
    else:

        base_path = Path(__file__).parent
    
    return base_path 


    

def get_new_flight_folder(source_path: Path) -> str:
    """On Drone Onboard computer a new flight is saved in config"""




# def do_later:
#     replaced_config = replace_config_placeholder(
#         config=config_dict, 
#         placeholder="{flight_folder}", 
#         replacement="re112o_250610")
#     resolved_config = resolve_relative_paths(
#         config=replaced_config, 
#         base_path=config_path.parent)
#     return resolved_config




if __name__ == "__main__":
    # Logger Settings
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [
            logging.StreamHandler()  # Force console output
        ]
    )
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    try:
        config_path = get_base_path() / "config.yaml"
        config = load_config_from_yamlfile(config_path)
    
        # Load Config
        if config['mode'] == "drone_to_hd":
            drone_to_hd_transfer(config)
        elif config['mode'] == "hd_to_drone":
            print("Mode: Hard Drive to Drone Transfer")
        else:
            raise ValueError(f"Invalid mode in config: {config['mode']}")

        logger.info("All transfers complete")
        logger.warning("Please unmount Drive before disconnecting!")

    except Exception as e:
        logger.error("Program failed: %s", e, exc_info=True)

    finally:
        input("\nPress Enter to exit...")











   
