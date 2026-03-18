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
        self.window_title: str = "POSPac UAV"# TODO: Remove window title and use auto_id instead
        self.auto_id: str = "MainFormBase"  
        self.is_idl_application: bool = False
    
    def _create_default_project(self, controlfinder: ControlFinder):
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
            auto_id="[Group : Project Tools] Tool : New - Index : 0 ") 
        btn.invoke()


    
    def _open_saveas_window(self, controlfinder: ControlFinder):
       controlfinder.window.type_keys("^s") # Ctrl + S is the shortcut to open Save As window 


    def _get_saveas_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        self._open_saveas_window(controlfinder)
        imageselection_window = controlfinder.find_child_window_by_title(
            window_title="Save As")
        return imageselection_window
    
    def _create_project(self, controlfinder: ControlFinder, output_folder: Path, project_name: str = "pospac_project"):
        self._create_default_project(controlfinder)
        saveas_cf = ControlFinder(window=self._get_saveas_window(controlfinder))

        # Write Path
        filename_editbox = saveas_cf.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        projec_folder = output_folder / project_name
        filename_editbox.set_edit_text(str(projec_folder))

        #Confirm to create project
        filename_editbox.type_keys("{ENTER}")

        # Wait for window to close
        saveas_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

        # Additional safety: ensure window is truly gone
        time.sleep(1)  # Small buffer to ensure cleanup



    def run(self):
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                auto_id=self.auto_id,
                                is_idl_application=self.is_idl_application) as pospac_manager:
            main_window_cf = ControlFinder(window=pospac_manager.window)
            main_window_cf.window.set_focus()


            
            
            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                print(output_folder)
                self._create_project(main_window_cf, output_folder)
                time.sleep(1)  # Wait for window to be focused
         
    


if __name__ == "__main__":
    pospacuav = PosPacUav(input_folders=[Path("E:/mjolnir_processing/RAW")],
                          output_folders=[Path("E:/mjolnir_processing/tmp")])
    
    pospacuav.run()
