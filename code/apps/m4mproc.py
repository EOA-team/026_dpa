"""Contains class to simulate M4MProc Windows Application """
import time
from pathlib import Path
from enum import Enum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)


class M4MProcStep(Enum):
        """Supported processing steps in M4MProc
        Checkbox Index is used to select the processing steps in the M4MProc GUI, 
        because the checkboxes are not uniquely identifiable by their names.
        (Name, Checkbox Index)"""

        RAW_DATA_IMPORT = ("Raw Data Import", 0)
        GEOCODING = ("Geocoding", 1)
        REFLECTANCE_RETRIEVAL = ("Reflectance Retrieval", 2)
        TOPOGRAPHIC_RADIOMETRIC_CORRECTION = ("Topographic Radiometric Correction", 3)
        PRODUCT_GENERATION = ("Product Generation", 4)
        ORTHORECTIFICATION = ("Orthorectification", 5)
        MOSAIC = ("Mosaic", 6)
        POINT_CLOUD = ("Point Cloud", 7)
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
    def __init__(self, input_folders: list[Path], output_folders: list[Path], selected_steps: list[M4MProcStep]):
        self.input_folders = input_folders
        self.output_folders = output_folders
        self.active_steps = selected_steps

        # Application
        self.app_path: str = "C:/ReSe_Software_Win/m4mproc/M4Mproc.exe"
        self.work_dir: str = "C:/ReSe_Software_Win/m4mproc/"
        # Window title stays static, no need for window_auto_id
        self.window_title: str = "ReSe Hyspex Processor 2025"
        self.is_idl_application: bool = True
    
    def set_processing_steps(self, controlfinder: ControlFinder, steps: list[M4MProcStep]) -> None:
        """Set the processing steps in the M4MProc GUI by checking/unchecking the corresponding checkboxes."""
        for step in list(M4MProcStep):
            checkbox = controlfinder.find_by_name(
                control_type="CheckBox",
                found_index=step.value[1]
            )
            checkbox_simulator = ControlSimulator(checkbox)
            if step in self.active_steps:
                checkbox_simulator.enable_checkbox()
            else:
                checkbox_simulator.disable_checkbox()

    def run(self):
        """Run M4MProc for each input/output folder pair (= job)."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                window_auto_id= None,
                                is_idl_application=self.is_idl_application) as m4mproc_manager:
            main_window_cf = ControlFinder(window=m4mproc_manager.window)

            main_window_cf.window.wait('enabled', timeout=DEFAULT_WAIT_TIME)
            main_window_cf.window.set_focus()
            m4mproc.set_processing_steps(controlfinder=main_window_cf, steps=[M4MProcStep.GEOCODING])
            time.sleep(5)


            # for input_folder, output_folder in zip(self.input_folders, self.output_folders):
            #     # Make sure Window is ready before starting next iteration
            #     main_window_cf.window.wait(
            #         'enabled', timeout=DEFAULT_WAIT_TIME)
            #     main_window_cf.window.set_focus()
            #     # Next iteration
            #     job_name = input_folder.parent.name
            #     # load config

                
                

if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW")]
    
    m4mproc = M4MProc_Application(input_folders=test_input_folders, 
                                  output_folders=test_output_folders,
                                  selected_steps=[M4MProcStep.GEOCODING])
    
    
    # Load Config

    # Set Steps 
    m4mproc.active_steps = [M4MProcStep.GEOCODING]
    m4mproc.run()
    


    #m4mproc.run()
    