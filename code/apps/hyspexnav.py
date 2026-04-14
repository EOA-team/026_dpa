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


    def _click_setup_button(self, controlfinder: ControlFinder) -> None:
        """Open the Setup frame."""
        btn = controlfinder.find_by_auto_id(
            control_type="CheckBox", # detected in UIA as checkbox, but it is a button!
            auto_id="HySpexNav.btnSetup")
        btn.invoke()

    def _click_load_settings_button(self, controlfinder: ControlFinder) -> None:
        """Click the 'Load Settings' button in the Setup frame."""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
                auto_id="HySpexNav.frameSetup.btnLoadSettings")
        btn.invoke()

    def _open_loadsettings_window(self, controlfinder: ControlFinder) -> None:
        """Open the 'Load Settings' window."""
        self._click_setup_button(controlfinder)
        time.sleep(0.5)  # Small wait to ensure the setup frame is loaded
        self._click_load_settings_button(controlfinder)

    def _get_loadsettings_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        imageselection_window = controlfinder.find_child_window_by_title(
            window_title="Open")
        return imageselection_window

    def _load_settings(self, controlfinder: ControlFinder, input_folder: Path):
        """ Select all input images from the specified folder in the image selection window."""
        self._open_loadsettings_window(controlfinder)
        settings_cf = ControlFinder(
            window=self._get_loadsettings_window(controlfinder))

        # Write Path
        filename_editbox = settings_cf.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(input_folder))
        filename_editbox.type_keys("{ENTER}")
    
        # Wait for window to close
        settings_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

        # Additional safety: ensure window is truly gone
        time.sleep(1)  # Small buffer to ensure cleanup

    def run(self):
        """Run HySpexRad with the specified settings for all input/output folder pairs (= jobs."""
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=None,  # Not needed when using auto_id
                                window_auto_id=self.window_auto_id,
                                is_idl_application=self.is_idl_application) as hyspexnav_manager:
            
            main_window_cf = ControlFinder(window=hyspexnav_manager.window)
            main_window_cf.window.wait(
                'enabled', timeout=DEFAULT_WAIT_TIME)
            
            settings_path = get_base_path(__file__).parent /"configs" / "conf_hyspex_nav.ini" 

            self._load_settings(main_window_cf, settings_path)

            time.sleep(7)
            
        





if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250610/tmp"),
                           Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW"),
                          Path("E:/mjolnir_processing/re112o_250918/RAW")]
    hyspexnav = HyspexNavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)

    hyspexnav.run()