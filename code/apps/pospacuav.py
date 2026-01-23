"""Contains class to simulate PosPac Windows Application """
import time
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)

class PosPacUav:
    """
    Class to simulate POSPac UAV which is only available as a Windows Application
    Allows to load the settings, start the processing and wait until process is finished.
    ️Note: POSPac UAV must be installed on the system where this code is executed.
    """


    def __init__(self, input_folders: list[Path], output_folders: list[Path]):
        self.input_folders = input_folders
        self.output_folders = output_folders

        # Application
        self.app_path: str = "C:/Program Files/Applanix/POSPac UAV 9.3/POSPacUAV.exe"
        self.work_dir: str = "C:/Program Files/Applanix/POSPac UAV 9.3/"
        self.window_title: str = "POSPac UAV"
        self.is_idl_application: bool = False

    def run(self):
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                is_idl_application=self.is_idl_application) as pospac_manager:
            main_window_cf = ControlFinder(window=pospac_manager.window)
            main_window_cf.window.set_focus()
            time.sleep(5)  # Wait for window to be focused

if __name__ == "__main__":
    pospacuav = PosPacUav(input_folders=[Path("E:/mjolnir_processing/RAW")],
                          output_folders=[Path("E:/mjolnir_processing/tmp")])
    
    pospacuav.run()
