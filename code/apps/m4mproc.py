"""Contains class to simulate M4MProc Windows Application """
import time
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)


class M4MProc_Application:
    """
    Class to simulate M4MProc which is only available as a Windows Application.
    M4mProc is a Beta Version of the Intacor Software. It integrates DROACOR and
    PARGE into one single processing software.

    The Processing Steps that are used in DPA are :
    1. Geocoding : Attaching a geographic coordinate system to the imagery
    2. Reflectance Retrieval : Converting the digital numbers to reflectance values (liighting and atmospheric correction)   
    3. Orthorectification : Uses a 3D terrain model to eliminate scale errors caused by uneven terrain and sensor tilt. 
    4. Mosaic : Stitch multiple images into a single image
    https://intacor.com/
    """

    def __init__(self, input_folders: list[Path], output_folders: list[Path]):
        self.input_folders = input_folders
        self.output_folders = output_folders

        # Application
        self.app_path: str = "C:/ReSe_Software_Win/m4mproc/M4Mproc.exe"
        self.work_dir: str = "C:/ReSe_Software_Win/m4mproc/"
        # Window title stays static, no need for window_auto_id
        self.window_title: str = "ReSe Hyspex Processor 2025"
        self.is_idl_application: bool = True

    def run(self):
        """Run M4MProc for each input/output folder pair (= job)."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                window_auto_id= None,
                                is_idl_application=self.is_idl_application) as m4mproc_manager:
            main_window_cf = ControlFinder(window=m4mproc_manager.window)
            time.sleep(5)  # Wait for the application to be fully loaded


if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW")]
    
    m4mproc = M4MProc_Application(input_folders=test_input_folders, output_folders=test_output_folders)
    m4mproc.run()
    