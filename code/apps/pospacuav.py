"""Contains class to simulate PosPac Windows Application """
import time
from shutil import copytree, rmtree
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)
from code.file_utils import wait_for_folder_stable

class PosPacUavApplication:
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
        self.window_auto_id: str = "MainFormBase"  # Identify by auto_id insted of window_title because title changes dynamically 
        self.is_idl_application: bool = False

    def initialize_default_project(self, output_folder: Path):
        output_folder.mkdir(parents=True, exist_ok=True)
        default_project_folder = Path(__file__).parent / "templates" / "default_pospac_project"
        output_project_folder = output_folder 
        copytree(src=default_project_folder, dst=output_project_folder, dirs_exist_ok=True)

    def _open_project_window(self, controlfinder: ControlFinder):
       controlfinder.window.wait('enabled', timeout=DEFAULT_WAIT_TIME)
       controlfinder.window.type_keys("^o") # Ctrl + O is the shortcut to open Open Project window 
    
    def _get_openproject_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        openproject_window = controlfinder.find_child_window_by_title(
            window_title="Open File") 
        return openproject_window
    
    def _enter_default_project_path(self, controlfinder: ControlFinder, output_folder: Path):
        filename_editbox = controlfinder.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        
        default_projecfile_path = output_folder / "pospac_tmp.pospac"
        filename_editbox.set_edit_text(str(default_projecfile_path))
        filename_editbox.type_keys("{ENTER}")
    
    def _open_default_project(self, controlfinder: ControlFinder, output_folder: Path):
        self._open_project_window(controlfinder)
        #Get new control finder for open project window
        openproject_window = self._get_openproject_window(controlfinder)
        open_project_cf = ControlFinder(window=openproject_window)
        # Enter default project path and open project
        self._enter_default_project_path(controlfinder=open_project_cf, 
                                         output_folder=output_folder)
        # Wait for window to close
        openproject_window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)
        time.sleep(1)  # Small buffer to ensure window is fully closed

    def _open_import_panel(self, controlfinder: ControlFinder):
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
            auto_id="[Group : Import Tools] Tool : Import - Index : 0 ") 
        btn.invoke()

    def _get_import_panel(self, controlfinder: ControlFinder) -> UIAWrapper:
        openproject_window = controlfinder.find_by_auto_id(
            control_type="Pane",
            auto_id= "ImportCmdUI"
        ) 
        return openproject_window

    def _set_import_folder(self, controlfinder: ControlFinder, import_folder: Path):
        filename_editbox = controlfinder.find_by_auto_id(
            control_type="Edit", auto_id="[Editor] Edit Area")
        filename_editbox.set_edit_text(str(import_folder))

    
    def _select_all_in_importlist(self, controlfinder: ControlFinder):
        import_list = controlfinder.find_by_auto_id(
            control_type="Table",
            auto_id="importList")
        ControlSimulator(import_list).select_all_rows()

    def _enable_close_panel_after_import(self, controlfinder: ControlFinder) -> None:
        checkbox = controlfinder.find_by_auto_id(
            control_type="CheckBox",
            auto_id="closeAfterImportBox")
        ControlSimulator(checkbox).enable_checkbox()

    def _import_selected_files(self, controlfinder: ControlFinder):
        controlfinder.window.type_keys("{ENTER}")

    def confirm_warnig_popup(self, controlfinder: ControlFinder):
        """After importing trajectory data, a warning popup appears, confirm it by pressing enter""" 
        controlfinder.window.type_keys("{ENTER}")

    def _wait_and_confirm_import_dialog(self,controlfinder: ControlFinder,
                                timeout: int = 240)-> None:
        """Wait until the import completion dialog appears
        Import Process takes ~3min --> when longer 4min--> issue."""
        import_dialog = controlfinder.window.child_window(auto_id="InternalMessageBox")
        import_dialog.wait('exists', timeout=timeout)
        import_dialog.type_keys("{ENTER}")
        print("Importing is Finished ")


    def _import_trajectory_data(self, controlfinder: ControlFinder, input_folder: Path, output_folder: Path):

        self._open_import_panel(controlfinder)
        #Get new control finder for open project window
        import_panel = self._get_import_panel(controlfinder)
        import_panel_cf = ControlFinder(window=import_panel)

        self._set_import_folder(
             controlfinder=import_panel_cf, 
             import_folder=input_folder / "apx")
        self._select_all_in_importlist(import_panel_cf)
        self._enable_close_panel_after_import(import_panel_cf)
        self._import_selected_files(import_panel_cf)

    def _save_project(self, controlfinder: ControlFinder) -> None:
        """Save current project state using Ctrl+S."""
        controlfinder.window.wait('enabled', timeout=DEFAULT_WAIT_TIME)
        controlfinder.window.type_keys("^s")
        
            
        




    def run(self):
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=None,  # Not needed when using auto_id
                                window_auto_id=self.window_auto_id,
                                is_idl_application=self.is_idl_application) as pospac_manager:
            main_window_cf = ControlFinder(window=pospac_manager.window)
            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                #Make sure Window is ready before starting next iteration
                main_window_cf.window.wait('enabled', timeout=DEFAULT_WAIT_TIME)
                main_window_cf.window.set_focus()
                #Next iteration
                self.initialize_default_project(output_folder) 
                self._open_default_project(main_window_cf, output_folder)
                self._import_trajectory_data(controlfinder = main_window_cf, 
                                             input_folder = input_folder, 
                                             output_folder = output_folder)
                self._wait_and_confirm_import_dialog(main_window_cf)
                self._save_project(main_window_cf)


                #Most often import has warnings, so confirm warning popup if it appears
                #self.confirm_warnig_popup(main_window_cf)
                
                
    
         
    


if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250610/tmp"), Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW"), Path("E:/mjolnir_processing/re112o_250918/RAW")]
    pospacuav = PosPacUavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)
    
    pospacuav.run()
    
