"""Contains class to simulate HySpexNav Windows Application """
import time
from pathlib import Path
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper, DEFAULT_WAIT_TIME
)
from code.file_utils import get_base_path, wait_for_file_count




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
        settings_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

    def _open_addfiles_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Open the 'Add Files' window to set the input files"""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
                auto_id="HySpexNav.splitter.layoutWidgetMain.btnInputFileAdd")
        btn.invoke()

    def _get_addfiles_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Get the 'Add Files' window after it has been opened."""
        imageselection_window = controlfinder.find_child_window_by_title(
            window_title="Open")
        return imageselection_window
        
    def _add_input_files(self, controlfinder: ControlFinder, input_folder: Path):
        """Add multiple input files via the Add Files window.
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
        filename_editbox.set_edit_text(str(input_folder))
        filename_editbox.type_keys("{ENTER}")

        # Mark all items
        itemslist = addfiles_cf.find_by_name(
            control_type="List", control_name="items view", exact=True)
        itemslist.type_keys("^a")  # Ctrl+A

        # Confirm Selection
        open_btn = addfiles_cf.find_by_auto_id(control_type="Button",
                                               auto_id="1")
        open_btn.click()
    
        # Wait for window to close
        addfiles_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)



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

    def _analyze_input_files(self, controlfinder: ControlFinder):
        """Click the 'Analyze' button to stage the flght lines based on the input files."""
        analyze_btn = controlfinder.find_by_auto_id(
            control_type="Button", auto_id="HySpexNav.splitter.layoutWidgetMain.btnAnalyze")
        analyze_btn.invoke()

    def _generate_output_files(self, controlfinder: ControlFinder):
        """Click the 'Generate Output' button to process the staged flight lines."""
        generate_btn = controlfinder.find_by_auto_id(
            control_type="Button", auto_id="HySpexNav.splitter.layoutWidgetFlightLines.btnGenerateOutput")
        generate_btn.invoke()

    def _clear_flightlines(self, controlfinder: ControlFinder):
        """Click the 'Clear Flight Lines' button to clear the staged flight lines for the next iteration."""
        clear_btn = controlfinder.find_by_auto_id(
            control_type="Button", auto_id="HySpexNav.splitter.layoutWidgetFlightLines.btnFlightLineClear")
        clear_btn.invoke()
    


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
                #Next Iteration
                self._set_output_folder(main_window_cf, output_folder)  
                output_folder.mkdir(parents=True, exist_ok=True)  # ensure output folder exists
                self._add_input_files(main_window_cf, input_folder)
                self._analyze_input_files(main_window_cf)
                time.sleep(1)  # Wait a bit to ensure analysis is done before generating output
                self._generate_output_files(main_window_cf)
                wait_for_file_count(folder=output_folder, expected_count=6, pattern="*.txt", timeout_s=10)  
                #Clear for next iteration
                self._clear_flightlines(main_window_cf)  
                self._clear_file_input(main_window_cf)  
                
                


if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250903/tmp/swirvnir"),
                           Path("E:/mjolnir_processing/re112o_250918/tmp/swirvnir")]
    test_input_folders = [Path("E:/mjolnir_processing/re112o_250903/tmp/input_hyspexnav"),
                          Path("E:/mjolnir_processing/re112o_250918/tmp/input_hyspexnav")]
    hyspexnav = HyspexNavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)

    hyspexnav.run()