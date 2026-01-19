"""
PyWinAuto Helper Module - An abstraction layer for the pywinauto library.
Provides helper functions to manage windows and find controls more easily.
"""

from pywinauto import Application, Desktop
from pywinauto.controls.uiawrapper import UIAWrapper

# Configure Module
DEFAULT_WAIT_TIME = 5
DEFAULT_BACKEND = "uia"

# Exceptions
class WindowAutomationError(Exception):
    """Base exception for window automation errors."""
    ...
class IdlHandlingError(WindowAutomationError):
    """Raised when there is an error handling IDL VM startup."""
    ...


class DesktopManager:
    def __init__(self, backend : str =DEFAULT_BACKEND):
        self.desktop = Desktop(backend=backend)

    def handle_idl_vm_startup(self,) -> None:
        """
        Handle IDL Virtual Machine startup dialog.
        IDL applications show a Runtime App window on startup that needs to be clicked.
        """
        try:
            idlvm_window = self.desktop.window(title='Runtime App')
            idlvm_window.wait('exists', timeout=DEFAULT_WAIT_TIME)
            pane = idlvm_window.child_window(control_type="Pane")
            pane.wait('exists', timeout=DEFAULT_WAIT_TIME)
            image = pane.child_window(auto_id="316", control_type="Image")
            image.wait('exists', timeout=DEFAULT_WAIT_TIME)
            image.click_input()
        except Exception as e:
            raise IdlHandlingError(f"Error handling IDL VM startup: {e}") from e
    
    def get_window(self, window_title, wait_time=DEFAULT_WAIT_TIME   ):
        window = self.desktop.window(title=window_title)
        window.wait('exists', timeout=wait_time)
        return window  

    def list_all_windows(self):
        """List all windows with details."""
        for window in self.desktop.windows():
            title = window.window_text()
            class_name = window.class_name()
            is_visible = window.is_visible()
            is_enabled = window.is_enabled()
            rect = window.rectangle()
            
            print(f"Title: {title}")
            print(f"Class: {class_name}")
            print(f"Visible: {is_visible}")
            print(f"Enabled: {is_enabled}")
            print(f"Position: {rect}")
            print("=" * 50)

class ApplicationManager:
    """Manages all the windows applications that are opened via pywinauto."""
    def __init__(self, app_path : str , window_title: str, backend :str =DEFAULT_BACKEND, 
                 is_idl_application: bool = False, work_dir: str |None = None):
        self.app_path = app_path
        self.window_title = window_title
        self.work_dir : str | None = work_dir
        self.backend = backend 
        self.is_idl_application = is_idl_application # Some applications  IDL VM that needs special handling
        self.app : Application | None = None
        self.window: UIAWrapper| None  = None

    def __enter__(self) -> "ApplicationManager":
        """Context manager start point - opens when entering 'with' block."""
        self.app = Application(backend=self.backend).start(cmd_line = self.app_path, 
                                                           work_dir = self.work_dir)
        # Some applications use IDL VM that needs special handling
        if self.is_idl_application:
            desktop_manager = DesktopManager()
            desktop_manager.handle_idl_vm_startup()
            self.window =desktop_manager.get_window(self.window_title, wait_time=DEFAULT_WAIT_TIME)
            self.app = Application(backend=self.backend).connect(handle=self.window.handle)
            return self 

        self.window = self.app.window(title=self.window_title)
        self.window.wait('exists', timeout=DEFAULT_WAIT_TIME)
        return self    


    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point - handles cleanup when leaving 'with' block."""
        if self.app:
            self.app.kill()

    