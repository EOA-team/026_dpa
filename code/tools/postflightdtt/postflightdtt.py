
import logging
from code.yamlconfig_helper import load_config_from_yamlfile
from code.tools.postflightdtt.drone_to_hd import drone_to_hd_transfer
from code.tools.postflightdtt.hd_to_nas import hd_to_nas_transfer
from code.file_utils import get_base_path

logger = logging.getLogger(__name__)


    

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
        config_path = get_base_path(__file__) / "config.yaml"
        config = load_config_from_yamlfile(config_path)
    
        # Load Config
        if config['mode'] == "drone_to_hd":
            drone_to_hd_transfer(config)
        elif config['mode'] == "hd_to_nas":
            hd_to_nas_transfer(config)
        else:
            raise ValueError(f"Invalid mode in config: {config['mode']}")

        logger.info("All transfers complete")
        logger.warning("Please unmount Drive before disconnecting!")

    except Exception as e:
        logger.error("Program failed: %s", e, exc_info=True)

    finally:
        input("\nPress Enter to exit...")











   
