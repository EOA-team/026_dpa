import logging
from code.yamlconfig_helper import load_config_from_yamlfile
from code.file_utils import get_base_path
from code.tools.thermsync.thermal_cam import ThermalCam
from pathlib import Path

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Logger Settings
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()  # Force console output
        ]
    )

    try:
        config_path = get_base_path(__file__) / "config.yaml"
        config = load_config_from_yamlfile(config_path)

        cam = ThermalCam(
            target_fps=config["target_fps"],
            out_dir=Path(config["destination_path"])
        )
        cam.prepare()
        logger.info("Connected to Thermal Camera...")

        cam.apply_default_config()
        logger.info("Loaded Default Config...")

        cam.start_acquiring()

        logger.info("Image Acquisition Started...")
        logger.info("Important! Wait 10min before Saving Geotiffs")

        while input("Press <s> + Enter to start sampling: ").strip().lower() != "s":
            print("  ⚠ Press S then Enter.")
        cam.set_nuc(mode="Manual")

        cam.stop_acquiring()
        cam.disconnect()





    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("Program failed: %s", e, exc_info=True)

    finally:
        input("\nPress Enter to exit...")








