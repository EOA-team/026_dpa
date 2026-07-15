"""Contains class to simulate M4MProc Windows Application """
import time
from pathlib import Path
from enum import Enum
from code.file_utils import get_base_path
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
    def __init__(self, input_folders: list[Path], output_folders: list[Path], selected_steps: list[M4MProcStep], config: Path):
        self.input_folders = input_folders
        self.output_folders = output_folders
        self.active_steps = selected_steps
        self._config = config

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
    
    @property
    def config(self) -> Path:
        return self._config
    
    @config.setter
    def config(self, value: Path) -> None:
        self._config = value

    def _expand_edit_tab(self, controlfinder: ControlFinder) -> None:
        """Expand the 'Edit' tab in the M4MProc GUI to access load config"""
        edit_tab = controlfinder.find_by_name(control_type="MenuItem", 
                                              control_name="Edit")
        edit_tab.expand()
    
    def _open_file_selector(self, controlfinder: ControlFinder) -> None:
        """Press the 'Load Config' MenuItem in the 'Edit' tab to open file selector"""
        self._expand_edit_tab(controlfinder)
        load_config= controlfinder.find_by_auto_id(control_type= "MenuItem", auto_id="1283")
        load_config.click_input()

    def _get_file_selector_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Get the file selector window that opens after pressing 'Load Config'"""
        file_selector_window = controlfinder.find_child_window_by_title(
            window_title="Please Select a File")
        return file_selector_window
    
    
    def _load_config(self, controlfinder: ControlFinder):
        """ Load settings from a json file  """
        self._open_file_selector(controlfinder)
        addfiles_cf = ControlFinder(
            window=self._get_file_selector_window(controlfinder))

        # Write Path
        filename_editbox = addfiles_cf.find_by_name(
            control_type="Edit", control_name="File name:", exact=True)
        filename_editbox.set_edit_text(str(self.config))
        filename_editbox.type_keys("{ENTER}")

        # Wait for window to close
        addfiles_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

    def _set_input_folder(self, controlfinder: ControlFinder, input_folder: Path) -> None:
        """Set the input folder in the M4MProc GUI."""
        input_folder_editbox = controlfinder.find_by_name(
            control_type="Edit",
            control_name="Main Input Directory")
        input_folder_editbox.set_edit_text(str(input_folder) + "\\")
        # The '\' is important otherwise SWIR and VNIR are not found'

    def _set_dsm_input_file(self, controlfinder: ControlFinder, input_folder: Path) -> None:
        """Set the input folder in the M4MProc GUI."""
        input_folder_editbox = controlfinder.find_by_name(
            control_type="Edit",
            control_name="DSM File")
        input_folder_editbox.set_edit_text(str(input_folder / "DSM" / "DSM"))


    def _set_output_folder(self, controlfinder: ControlFinder, output_folder: Path) -> None:
        """Set the output folder in the M4MProc GUI."""
        output_folder_editbox = controlfinder.find_by_name(
            control_type="Edit",
            control_name="Output directory")
        output_folder_editbox.set_edit_text(str(output_folder))


    def set_paths(self, controlfinder: ControlFinder, input_folder: Path, output_folder: Path) -> None:
        """Set the input and output folders/files in the M4MProc GUI."""
        self._set_input_folder(controlfinder, input_folder)
        self._set_dsm_input_file(controlfinder, input_folder)
        self._set_output_folder(controlfinder, output_folder)

    def start_process(self, controlfinder: ControlFinder) -> None:
        """Start the M4MProc process."""
        start_btn = controlfinder.find_by_name(
            control_type="Button",
            control_name="Process")
        start_btn.click()


    def confirm_process_start(self, controlfinder: ControlFinder) -> None:
        """M4MProc shows a confirmation dialog before starting the process. This method confirms the dialog."""
        controlfinder.debug_print_controls()
        idl_alert_window = controlfinder.find_child_window_by_title(window_title="IDL Control Window")
        idl_alert_window.wait('exists', timeout=DEFAULT_WAIT_TIME)
        idl_alert_cf = ControlFinder(window=idl_alert_window)
        idl_alert_cf.debug_print_controls()
        ok_btn = idl_alert_cf.find_by_name(control_type="Button", control_name="OK")
        ok_btn.click()

    def run(self):
        """Run M4MProc for each input/output folder pair (= job)."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                window_auto_id= None,
                                is_idl_application=self.is_idl_application) as m4mproc_manager:
            main_window_cf = ControlFinder(window=m4mproc_manager.window)

            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                # Make sure Window is ready before starting next iteration
                main_window_cf.window.wait(
                    'enabled', timeout=DEFAULT_WAIT_TIME)
                main_window_cf.window.set_focus()

                # Next iteration
                self._load_config(controlfinder=main_window_cf)
                self.set_processing_steps(controlfinder=main_window_cf, steps=self.active_steps)
                self.set_paths(controlfinder=main_window_cf, 
                                 input_folder=input_folder, 
                                 output_folder=output_folder)
                self.start_process(controlfinder=main_window_cf)
                self.confirm_process_start(controlfinder=main_window_cf)
                time.sleep(30)
            
        

                
                

if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250918/output")]
    test_input_folders = [Path("E:/mjolnir_processing/re112o_250918")]

    config_path = get_base_path(__file__).parent / "configs" / "conf_m4mproc_radiance.json"
    
    m4mproc = M4MProc_Application(input_folders=test_input_folders, 
                                  output_folders=test_output_folders,
                                  selected_steps=[M4MProcStep.GEOCODING],
                                  config=config_path)

    
    m4mproc.run()
    
    