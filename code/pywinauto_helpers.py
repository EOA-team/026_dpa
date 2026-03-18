"""
PyWinAuto Helper Module - An abstraction layer for the pywinauto library.
Provides helper functions to manage windows and find controls more easily.
"""

from pywinauto import Application, Desktop  # type: ignore[import-untyped]
from pywinauto.controls.uiawrapper import UIAWrapper # type: ignore[import-untyped]

# Configure Module
DEFAULT_WAIT_TIME = 5
DEFAULT_BACKEND = "uia"
IDL_VM_WINDOW_TITLE = "Runtime App"

# Exceptions


class WindowAutomationError(Exception):
    """Base exception for window automation errors."""
    ...  # pylint: disable=unnecessary-ellipsis


class IdlHandlingError(WindowAutomationError):
    """Raised when there is an error handling IDL VM startup."""
    ...  # pylint: disable=unnecessary-ellipsis


class ControlNotFoundError(WindowAutomationError):
    """Raised when a UI control cannot be found."""
    ...  # pylint: disable=unnecessary-ellipsis


class WindowNotFoundError(WindowAutomationError):
    """Raised when a Window cannot be found."""
    ...  # pylint: disable=unnecessary-ellipsis


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
    the application is properly started and closed.
    
    Note on window identification:
        Different applications expose their main window differently via UI Automation.
        Some applications provide a stable automation ID for their main
        window, which is the preferred way to identify it. Other applications 
        do not expose an automation ID for the main window and must be identified by title.
        This can be critical if  the window titles change dynamically during runtime.
        At least one of 'window_title' or 'window_auto_id' must therefore be provided!
    """

    def __init__(self, app_path: str, window_title: str | None, window_auto_id: str | None , 
                 is_idl_application: bool = False, work_dir: str | None = None):
        if not window_title and not window_auto_id:
            raise ValueError("At least one of 'window_title' or 'window_auto_id' must be provided.")
        self.app_path = app_path
        self.window_title = window_title
        self.window_auto_id = window_auto_id
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

        # Identify main window either by auto_id or title depending on what is provided
        if self.window_auto_id:
            self.window = self.app.window(auto_id=self.window_auto_id)
        else:
            self.window = self.app.window(title=self.window_title)

        self.window.wait('exists', timeout=DEFAULT_WAIT_TIME)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point - handles cleanup when leaving 'with' block."""
        if self.app:
            self.app.kill()


class ControlFinder:
    """Provides methods to find controls within a given window.
    There are two matching strategies:
    - By auto_id: Savest way if available, because unique and does not change so often (SW updates).
      Note:Unfortunately not always available in all applications.
      For example, in IDL applications most controls do not have an auto_id.
    - By name: Sometimes controls do not have unique names. 
    In this case we can specify which occurrence to return by found_index .
    """

    def __init__(self, window: UIAWrapper):
        self.window = window

    @staticmethod
    def _matches_name(control_text: str, target_name: str, exact: bool) -> bool:
        """Check if control text matches the target name."""
        if not target_name:
            return True
        control_text_norm = control_text.strip().lower()
        target_name_norm = target_name.strip().lower()
        if exact:
            return control_text_norm == target_name_norm
        return target_name_norm in control_text_norm

    def _get_matches_by_name(
        self,
        control_type: str,
        control_name: str,
        exact: bool
    ) -> list[UIAWrapper]:
        """
        Get all controls matching the specified type and name.
        """
        matching_controls = []
        all_controls_of_type = []

        for ctrl in self.window.descendants():
            if ctrl.element_info.control_type != control_type:
                continue
            control_text = ctrl.window_text().strip()
            all_controls_of_type.append(control_text)
            if self._matches_name(control_text, control_name, exact):
                matching_controls.append(ctrl)
        if not matching_controls:
            match_type = "exact" if exact else "partial"
            name_info = f" with name '{control_name}' ({match_type})" if control_name else ""
            error_msg = f"Could not find {control_type}{name_info}\n"
            error_msg += f"Available {control_type} controls found: {all_controls_of_type}"
            raise ValueError(error_msg)

        return matching_controls

    def _get_match_by_auto_id(
        self,
        control_type: str,
        auto_id: str
    ) -> UIAWrapper:
        """
        Get control matching the specified AutomationId.
        """
        matching_controls = []
        all_auto_ids = []

        for ctrl in self.window.descendants():
            if ctrl.element_info.control_type != control_type:
                continue

            ctrl_auto_id = ctrl.element_info.automation_id

            if ctrl_auto_id:  # Only collect non-empty AutomationIds
                all_auto_ids.append(ctrl_auto_id)

            if ctrl_auto_id == auto_id:
                matching_controls.append(ctrl)

        if not matching_controls:
            error_msg = f"Could not find control with auto_id '{auto_id}'\n"
            error_msg += f"Available AutomationIds found: {sorted(set(all_auto_ids))}"
            raise ControlNotFoundError(error_msg)

        if len(matching_controls) > 1:
            raise ControlNotFoundError(
                f"Found {len(matching_controls)} controls with auto_id='{auto_id}'. "
                f"AutomationId should be unique but found duplicates."
            )

        return matching_controls[0]

    def find_by_name(
        self,
        control_type: str,
        control_name: str = "",
        exact: bool = False,
        found_index: int = 0,  # by default take first found  control

    ) -> UIAWrapper:
        """
        Find a UI control by type and name.
        Examples:
            # Find button (partial match)
            btn = manager.find_control(
                window=window, control_type="Button", control_name="Submit"
            )
            # Find button (exact match)
            btn = manager.find_control(
                window=window, control_type="Button", 
                control_name="Submit", exact=True
            )
            # Find second ComboBox named "Save"
            combo = manager.find_control(
                window=window, control_type="ComboBox", 
                control_name="Save", exact=True, found_index=1
            )
            # Find second ListBox (any name)
            listbox = manager.find_control(
                window=window, control_type="ListBox", found_index=1
            )
        """
        # Bring window to foreground to ensure controls are accessible
        self.window.set_focus()
        matching_controls = self._get_matches_by_name(
            control_type, control_name, exact)
        return matching_controls[found_index]

    def find_all_by_name(
        self,
        control_type: str,
        control_name: str = "",
        exact: bool = False,
    ) -> list[UIAWrapper]:
        """
        Find all UI controls matching type and name.

        Examples:
            # Get all ComboBoxes named "Software Binning"
            all_combos = manager.find_all_by_name(
                control_type="ComboBox", 
                control_name="Software Binning"
            )
        """
        self.window.set_focus()
        matching_controls = self._get_matches_by_name(
            control_type, control_name, exact)
        return matching_controls

    def find_by_auto_id(
        self,
        control_type: str,
        auto_id: str,
    ) -> UIAWrapper:
        """
        Find a UI control by AutomationId.

        Examples:
            # Find button by AutomationId
            button = manager.find_control_by_auto_id(auto_id="btnSubmit")

            # Find edit control
            edit = manager.find_control_by_auto_id(auto_id="txtUsername")
        """
        # Bring window to foreground to ensure controls are accessible
        self.window.set_focus()

        # Find all matching controls
        matching_control = self._get_match_by_auto_id(
            auto_id=auto_id, control_type=control_type)

        return matching_control

    def find_child_window_by_title(self, window_title: str) -> UIAWrapper | None:
        """
        Search for a visible child window within the parent window.
        """
        # Look for child window
        child_window = self.window.child_window(
            control_type="Window", title=window_title)
        if child_window.exists(timeout=DEFAULT_WAIT_TIME):
            return child_window
        raise WindowNotFoundError(
            f"Could not find child window with title '{window_title}'")


class ControlSimulator:
    """Provides an abstraction layer for some control simulations."""

    def __init__(self, control: UIAWrapper):
        self.control = control

    def enable_checkbox(self) -> None:
        """Enable/check the checkbox if it's not already checked."""
        if not hasattr(self.control, 'get_toggle_state'):
            raise AttributeError(
                "Control does not support toggle state (not a checkbox/toggle button)")

        if self.control.get_toggle_state() != 1:
            self.control.click()

    def disable_checkbox(self) -> None:
        """Disable/uncheck the checkbox if it's not already unchecked."""
        if not hasattr(self.control, 'get_toggle_state'):
            raise AttributeError(
                "Control does not support toggle state (not a checkbox/toggle button)")

        if self.control.get_toggle_state() != 0:
            self.control.click()
