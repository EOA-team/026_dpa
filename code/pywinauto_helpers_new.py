"""
PyWinAuto Helper Module - An abstraction layer for the pywinauto library.
Provides helper functions to manage windows and find controls more easily.
"""

from pywinauto import Application, Desktop # type: ignore[import-untyped]
from pywinauto.controls.uiawrapper import UIAWrapper # type: ignore[import-untyped]

# Configure Module
DEFAULT_WAIT_TIME = 5
DEFAULT_BACKEND = "uia"
IDL_VM_WINDOW_TITLE = "Runtime App"

# Exceptions


class WindowAutomationError(Exception):
    """Base exception for window automation errors."""
    ... # pylint: disable=unnecessary-ellipsis


class IdlHandlingError(WindowAutomationError):
    """Raised when there is an error handling IDL VM startup."""
    ... # pylint: disable=unnecessary-ellipsis


class DesktopManager:
    """It has access to all the windows currently open on the desktop and allows to open windows,
    that are not bound to a specific application instance. This is useful if an application spawns
    independent windows that need to be managed separately."""

    def __init__(self):
        self.desktop = Desktop(backend=DEFAULT_BACKEND)

    def handle_idl_vm_startup(self,) -> None:
        """
        Handle IDL Virtual Machine startup dialog.
        IDL applications show a Runtime App window on startup that needs to be clicked.
        """
        try:
            idlvm_window = self.desktop.window(title=IDL_VM_WINDOW_TITLE)
            idlvm_window.wait('exists', timeout=DEFAULT_WAIT_TIME)
            pane = idlvm_window.child_window(control_type="Pane")
            pane.wait('exists', timeout=DEFAULT_WAIT_TIME)
            image = pane.child_window(auto_id="316", control_type="Image")
            image.wait('exists', timeout=DEFAULT_WAIT_TIME)
            image.click_input()
        except Exception as e:
            raise IdlHandlingError(
                f"Error handling IDL VM startup: {e}") from e

    def get_window(self, window_title, wait_time=DEFAULT_WAIT_TIME):
        """Get a window by its title."""
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
    """Manages a Window application lifecycle using a context manager. This ensures that
    the application is properly started and closed."""

    def __init__(self, app_path: str, window_title: str,
                 is_idl_application: bool = False, work_dir: str | None = None):
        self.app_path = app_path
        self.window_title = window_title
        self.work_dir: str | None = work_dir
        # Some applications use IDL VM that needs special handling
        self.is_idl_application = is_idl_application
        self.app: Application | None = None
        self.window: UIAWrapper | None = None

    def __enter__(self) -> "ApplicationManager":
        """Context manager start point - opens when entering 'with' block."""
        self.app = Application(backend=DEFAULT_BACKEND).start(cmd_line=self.app_path,
                                                           work_dir=self.work_dir)
        # Some applications use IDL VM that needs special handling
        if self.is_idl_application:
            desktop_manager = DesktopManager()
            desktop_manager.handle_idl_vm_startup()
            self.window = desktop_manager.get_window(
                self.window_title, wait_time=DEFAULT_WAIT_TIME)
            self.app = Application(backend=DEFAULT_BACKEND).connect(
                handle=self.window.handle)
            return self

        self.window = self.app.window(title=self.window_title)
        self.window.wait('exists', timeout=DEFAULT_WAIT_TIME)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point - handles cleanup when leaving 'with' block."""
        if self.app:
            self.app.kill()
