"""Contains class to simulate HySpexNav Windows Application """
import time
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)


class HyspexNavApplication:
    """Automates the HySpex NAV desktop application via pywinauto.

    Discretizes a continuous IMU/GPS stream against sensor trigger events,
    producing one navigation file per flight line per sensor.

    Note:
        HySpex NAV must be installed on the system where this code is executed.
        Windows-only, requires pywinauto.
    """





    def __init__(self, input_folders: list[Path], output_folders: list[Path]):
        self.input_folders = input_folders
        self.output_folders = output_folders

        # Application
        self.app_path: str = "G:/02. HySpex software/HySpex NAV v2.6.1/HySpexNavGui.exe"
        self.work_dir: str = "G:/02. HySpex software/HySpex NAV v2.6.1/"
        self.window_auto_id: str = "HySpexNav"
        self.is_idl_application: bool = False






    def run(self):
        """Run HySpexRad with the specified settings for all input/output folder pairs (= jobs."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=None,  # Not needed when using auto_id
                                window_auto_id=self.window_auto_id,
                                is_idl_application=self.is_idl_application) as hyspexnav_manager:
            main_window_cf = ControlFinder(window=hyspexnav_manager.window)
            main_window_cf.window.set_focus()
            time.sleep(5)

if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250610/tmp"),
                           Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW"),
                          Path("E:/mjolnir_processing/re112o_250918/RAW")]
    hyspexnav = HyspexNavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)

    hyspexnav.run()