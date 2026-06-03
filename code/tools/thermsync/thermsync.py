import logging
from code.yamlconfig_helper import load_config_from_yamlfile
from code.file_utils import get_base_path
from code.tools.thermsync.thermal_cam import ThermalCam
from code.tools.thermsync.nmea_reader import NmeaReader, ZDA, PASHR, GGA, PTNLAVR
from pathlib import Path
import time
from code.tools.thermsync.keypress_listener import KeypressListener


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

        nmea = NmeaReader()
        nmea.connect()

        cam = ThermalCam(
            target_fps=config["target_fps"],
            out_dir=Path(config["destination_path"])
        )
        cam.prepare()
        logger.info("Connected to Thermal Camera...")

        cam.apply_default_config()
        logger.info("Loaded Default Config...")

        # Fetch Metadata before sampling
        camera_metadata = cam.fetch_metadata()
        cam.save_metadata_as_csv(
            filename=f"thermalcamara_metadata",
            metadata=camera_metadata,
            save_readme=True
        )
        logger.info("Save Initial Thermal Camera Metadata...")

        cam.start_acquiring()

        logger.info("Image Acquisition Started...")
        logger.info("Important! Wait 10min before Saving Geotiffs")

        while input("Press <s> + Enter to start sampling: ").strip().lower() != "s":
            print("  ⚠ Press S then Enter.")
        cam.set_nuc(mode="Manual")

        print("To quit Sampling press <q>")

        listener = KeypressListener(quit_key="q")
        listener.start()


        frame_idx = 0
        while not listener.quit_requested:
            t0 = time.perf_counter()

            #Get Raw image from Buffer
            with cam.image_acquirer.fetch(timeout=cam.buffer_timeout) as buffer:
                # Read Nmea stream
                nmea.drain()
                zda_sentence =nmea.get_latest(ZDA)
                pashr_sentence = nmea.get_latest(PASHR)
                gga_sentence = nmea.get_latest(GGA)
                ptnlavr_sentence= nmea.get_latest(PTNLAVR)
                timestamp = nmea.get_timestamp(zda=zda_sentence)

                component = buffer.payload.components[0]
                raw_image = component.data.reshape(component.height, component.width).copy()

            #Get Thermal Camera Metadata
            camera_metadata = cam.fetch_metadata()

            #Transform Raw to Celsius
            celsius_image = cam.raw_to_celsius(thermal_image=raw_image)



            #Save Files
            cam.save_tiff(thermal_image=raw_image, filename=f"{timestamp}_raw")
            cam.save_tiff(thermal_image=celsius_image, filename=f"{timestamp}_celsius")
            cam.save_metadata_as_csv(
                filename = f"{timestamp}_thermalcamara_metadata",
                metadata=camera_metadata,
                save_readme=False
            )


            nmea.save_sentence_to_csv(
                sentence=zda_sentence,
                filename=f"{timestamp}_metadata_zda",
                path=cam._out_dir)

            nmea.save_sentence_to_csv(
                sentence=pashr_sentence,
                filename=f"{timestamp}_metadata_pashr",
                path=cam._out_dir)

            nmea.save_sentence_to_csv(
                sentence=gga_sentence,
                filename=f"{timestamp}_metadata_gga",
                path=cam._out_dir)

            nmea.save_sentence_to_csv(
                sentence=ptnlavr_sentence,
                filename=f"{timestamp}_metadata_prnlavr",
                path=cam._out_dir)


            logger.info("Image written at {ts_str}")


            frame_idx += 1
            elapsed = time.perf_counter() - t0


            time.sleep(max(0, cam.sampling_period - elapsed))

        logger.info(f"Capture complete. {frame_idx} frames saved.")
        listener.stop()
        cam.set_nuc(mode="Automatic")
        cam.stop_acquiring()
        cam.disconnect()
        nmea.stop()





    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("Program failed: %s", e, exc_info=True)

    finally:
        input("\nPress Enter to exit...")








