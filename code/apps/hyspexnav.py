"""Contains class to simulate HySpexNav Windows Application """
import time
from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)
from code.file_utils import get_base_path


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


    def _open_setup_frame(self, controlfinder: ControlFinder) -> None:
        """Open the Setup frame to configure input file patterns.
        The Setup frame defines which file patterns HySpex NAV uses to
        automatically detect events, navigation outputs, and log files.
        Note:
            The Setup control is a CheckBox in UIA but behaves as a toggle button.
        """
        checkbox = controlfinder.find_by_auto_id(
            control_type="CheckBox", # detected in UIA as checkbox, but it is a button!
            auto_id="HySpexNav.btnSetup")
        
        checkbox_simulator = ControlSimulator(checkbox)
        checkbox_simulator.enable_checkbox()


    def _click_load_settings_button(self, controlfinder: ControlFinder) -> None:
        """Click the 'Load Settings' button in the Setup frame."""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
                auto_id="HySpexNav.frameSetup.btnLoadSettings")
        btn.invoke()

    def _open_loadsettings_window(self, controlfinder: ControlFinder) -> None:
        """Open the 'Load Settings' window."""
        self._open_setup_frame(controlfinder)
        time.sleep(0.5)  # Small wait to ensure the setup frame is loaded
        self._click_load_settings_button(controlfinder)

    def _get_loadsettings_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Get the 'Load Settings' window after it has been opened."""
        imageselection_window = controlfinder.find_child_window_by_title(
            window_title="Open")
        return imageselection_window

    def _load_settings(self, controlfinder: ControlFinder, input_file: Path):
        """ Load settings from a input file (*.ini file) """
        self._open_loadsettings_window(controlfinder)
        settings_cf = ControlFinder(
            window=self._get_loadsettings_window(controlfinder))

        # Write Path
        filename_editbox = settings_cf.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(input_file))
        filename_editbox.type_keys("{ENTER}")
    
        # Wait for window to close
        #settings_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

        # Additional safety: ensure window is truly gone
        time.sleep(2)  # Small buffer to ensure cleanup

    def _open_addfiles_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Open the 'Add Files' window to set the input files"""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
                auto_id="HySpexNav.splitter.layoutWidgetMain.btnInputFileAdd")
        btn.invoke()
        print("Add button clicked")

    def _get_addfiles_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Get the 'Add Files' window after it has been opened."""
        imageselection_window = controlfinder.find_child_window_by_title(
            window_title="Open")
        return imageselection_window
        
    def _add_input_file(self, controlfinder: ControlFinder, input_file: Path):
        """Add a single input file via the Add Files window.
        Supported types: 
            events.txt, 
            VNIR_all_records.txt,
            SWIR_all_records.txt, 
            {job_name}.log"""
        self._open_addfiles_window(controlfinder)
        addfiles_cf = ControlFinder(
            window=self._get_addfiles_window(controlfinder))

        # Write Path
        filename_editbox = addfiles_cf.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(input_file))
        filename_editbox.type_keys("{ENTER}")
    
        # Wait for window to close
        #addfiles_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

        # Additional safety: ensure window is truly gone
        time.sleep(2)  # Small buffer to ensure cleanup

    def _clear_file_input(self, controlfinder: ControlFinder):
        """Clear the file input list in the main window."""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
                auto_id="HySpexNav.splitter.layoutWidgetMain.btnInputFileClear")
        btn.invoke()


    def _set_output_folder(self, controlfinder: ControlFinder, output_folder: Path):
        """Set the output folder in the main window."""
        output_folder_editbox = controlfinder.find_by_auto_id(
            control_type="Edit", auto_id="HySpexNav.splitter.layoutWidgetMain.iOutputFolder")

        output_folder_editbox.set_edit_text(str(output_folder))


    def run(self):
        """Run HySpexRad with the specified settings for all input/output folder pairs (= jobs."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=None,  # Not needed when using auto_id
                                window_auto_id=self.window_auto_id,
                                is_idl_application=self.is_idl_application) as hyspexnav_manager:
            main_window_cf = ControlFinder(window=hyspexnav_manager.window)
            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                # Make sure Window is ready before starting next iteration
                main_window_cf.window.wait(
                    'enabled', timeout=DEFAULT_WAIT_TIME)
                main_window_cf.window.set_focus()
                # Reset Settings before next iteration
                settings_path = get_base_path(__file__).parent /"configs" / "conf_hyspex_nav.ini" 
                self._load_settings(main_window_cf, settings_path)
                # Set Input Files
                events_file = input_folder / "tmp" / f"{input_folder.name}_full_processing"/ "Mission 1"/ "Export"/ "events.txt"
                swir_records_file = input_folder / "tmp" / f"{input_folder.name}_full_processing"/ "Mission 1"/ "Export"/ "SWIR_all_records.txt"
                vnir_records_file = input_folder / "tmp" / f"{input_folder.name}_full_processing"/ "Mission 1"/ "Export"/ "VNIR_all_records.txt"
                log_file = input_folder / "RAW" / f"{input_folder.name}.log"
                input_files = [events_file, swir_records_file, vnir_records_file, log_file]
                

                #Next Iteration
                self._set_output_folder(main_window_cf, output_folder)  # Assuming same output folder for all jobs
                for input_file in input_files:
                    self._add_input_file(main_window_cf, input_file)
                    print(input_files)
                
                time.sleep(2)
                self._clear_file_input(main_window_cf)  # Clear input list for next iteration

            time.sleep(7)
            

        

        





if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250610/tmp"),
                           Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610"),
                          Path("E:/mjolnir_processing/re112o_250918")]
    hyspexnav = HyspexNavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)

    hyspexnav.run()