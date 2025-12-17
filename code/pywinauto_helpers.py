"""
PyWinAuto Helper Module

Common utility functions for Windows GUI automation using pywinauto.
Consolidates frequently used operations for window management, control finding,
and dialog handling.
"""
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper

# Default timeout for wait operations (seconds)
DEFAULT_WAIT_TIME = 3


def get_application(
    desktop: Desktop,
    window_title: str,
    wait_time: int = DEFAULT_WAIT_TIME
) -> UIAWrapper | None :
    """
    Check if an application window already exists.
    """
    tmp_window = desktop.window(title=window_title)
    if tmp_window.exists(timeout=wait_time):
        print(f"Window '{window_title}' already exists!")
        return tmp_window
    print(f"Window '{window_title}' does not exist.")
    return None
def handle_idl_vm_startup(
    desktop: Desktop,
    wait_time: int = DEFAULT_WAIT_TIME
) -> None:
    """
    Handle IDL Virtual Machine startup dialog.
    IDL applications show a Runtime App window on startup that needs to be clicked.
    """
    try:
        idlvm_window = desktop.window(title='Runtime App')
        idlvm_window.wait('exists', timeout=wait_time)
        pane = idlvm_window.child_window(control_type="Pane")
        pane.wait('exists', timeout=wait_time)
        image = pane.child_window(auto_id="316", control_type="Image")
        image.wait('exists', timeout=wait_time)
        image.click_input()
        print("✓ IDL VM startup handled")
    except Exception as e:
        print(f"⚠️ Error handling IDL VM startup: {e}")
        raise
def open_application(
    desktop: Desktop,
    app_path: str,
    window_title: str,
    work_dir: str | None = None,
    idl_application: bool = False,
    wait_time: int = DEFAULT_WAIT_TIME
) -> UIAWrapper:
    """
    Open an application or return existing window if already running.
    """
    # First check if application already exists
    existing_window = get_application(desktop, window_title, wait_time)
    if existing_window:
        return existing_window
    print(f"Opening application: {app_path}")
    Application(backend="uia").start(app_path, work_dir=work_dir)
    # Handle IDL VM startup if needed
    if idl_application:
        handle_idl_vm_startup(desktop, wait_time)
    window = desktop.window(title=window_title)
    window.wait('exists', timeout=wait_time)
    window.set_focus()
    print(f"✓ Application '{window_title}' opened successfully")
    return window

def _matches_control_name(control_text: str, target_name: str, exact: bool) -> bool:
    """Check if control text matches the target name."""
    if not target_name:
        return True
    control_text_norm = control_text.strip().lower()
    target_name_norm = target_name.strip().lower()
    if exact:
        return control_text_norm == target_name_norm
    return target_name_norm in control_text_norm

def _get_matching_controls(
    window: UIAWrapper,
    control_type: str,
    control_name: str,
    exact: bool
) -> list[UIAWrapper]:
    """
    Get all controls matching the specified type and name.
    
    """
    matching_controls = []
    all_controls_of_type = []

    for ctrl in window.descendants():
        if ctrl.element_info.control_type != control_type:
            continue
        control_text = ctrl.window_text().strip()
        all_controls_of_type.append(control_text)
        if _matches_control_name(control_text, control_name, exact):
            matching_controls.append(ctrl)
    if not matching_controls:
        match_type = "exact" if exact else "partial"
        name_info = f" with name '{control_name}' ({match_type})" if control_name else ""
        error_msg = f"Could not find {control_type}{name_info}\n"
        error_msg += f"Available {control_type} controls found: {all_controls_of_type}"
        raise ValueError(error_msg)

    return matching_controls


def find_control(
    window: UIAWrapper,
    control_type: str,
    control_name: str = "",
    exact: bool = False,
    found_index: int  = 0, # by default take first found  control

) -> UIAWrapper:
    """
    Find a UI control by type and name.
    Examples:
        # Find button (partial match)
        btn = find_control(
            window=window, control_type="Button", control_name="Submit"
        )
        # Find button (exact match)
        btn = find_control(
            window=window, control_type="Button", 
            control_name="Submit", exact=True
        )
        # Find second ComboBox named "Save"
        combo = find_control(
            window=window, control_type="ComboBox", 
            control_name="Save", exact=True, found_index=1
        )
        # Find second ListBox (any name)
        listbox = find_control(
            window=window, control_type="ListBox", found_index=1
        )
    """
    # Bring window to foreground to ensure controls are accessible
    window.set_focus()
    matching_controls = _get_matching_controls(window, control_type, control_name, exact)
    return matching_controls[found_index]


def _find_confirmation_window(window: UIAWrapper) -> UIAWrapper | None:
    """
    Search for a visible confirmation dialog or window within the parent window.
    """
    # Look for child window
    child_window = window.child_window(control_type="Window")
    if child_window.exists(timeout=DEFAULT_WAIT_TIME):
        print(f"  Found confirmation window: '{child_window.window_text()}'")
        return child_window

    # Look for child dialog
    child_dialog = window.child_window(control_type="Dialog")
    if child_dialog.exists(timeout=DEFAULT_WAIT_TIME):
        print(f"  Found confirmation dialog: '{child_dialog.window_text()}'")
        return child_dialog

    return None

def _click_confirmation_button(
    confirmation_window: UIAWrapper,
    confirmation_buttons: list[str]
) -> bool:
    """
    Try to click one of the confirmation buttons in the dialog/window.
    
    """
    for btn_name in confirmation_buttons:
        try:
            btn = find_control(
                window=confirmation_window,
                control_type="Button",
                control_name=btn_name,
                exact=False,
            )
            btn.invoke()
            return True

        except ValueError:
            # Button not found, try next one
            continue

    return False


def close_window_with_confirmation(
    window: UIAWrapper,
    confirmation_buttons: list[str],
) -> bool:
    """
    Close a window and automatically handle confirmation dialog if it appears.
    Also works for windows that close immediately without confirmation.

    Examples:
        # Must specify which button(s) to click
        close_window_with_confirmation(
            window, desktop, confirmation_buttons=["Yes"]
        )
        
        # Try multiple buttons in order
        close_window_with_confirmation(
            window, desktop, 
            confirmation_buttons=["Don't Save", "No", "OK"]
        )
        
        # Custom wait time
        close_window_with_confirmation(
            window, desktop, confirmation_buttons=["Yes"], 
            wait_for_dialog=2.0
        )
    """

    # Bring window to foreground to ensure controls are accessible
    window.set_focus()

    # Attempt to close the window
    print(f"Closing window: '{window.window_text()}'")
    window.close()
    conf_window = _find_confirmation_window(window=window)
    if not conf_window:
        print("  ✓ Window closed immediately (no confirmation needed)")
        return True
    click_sucess = _click_confirmation_button(confirmation_window=conf_window,
                                              confirmation_buttons= confirmation_buttons)
    return click_sucess



def set_checkbox(
    window: UIAWrapper,
    checkbox_name: str,
    activate: bool,
    exact: bool = False
) -> bool:
    """
    Check or uncheck a checkbox by name.
  
    Examples:
        # Check a checkbox
        set_checkbox(window, "Geocoding", activate=True)
        
        # Uncheck a checkbox
        set_checkbox(window, "Raw Data Import", activate=False)
        
        # Partial match
        set_checkbox(window, "Reflectance", activate=True)
        
        # Exact match
        set_checkbox(window, "Geocoding", activate=True, exact=True)
    """
    checkbox = find_control(window, "CheckBox", checkbox_name, exact=exact)

    if not checkbox:
        print(f"⚠️ Checkbox not found: '{checkbox_name}'")
        return False

    current_state = checkbox.get_toggle_state()  # 0=Off, 1=On
    desired_state = 1 if activate else 0

    # Already in desired state
    if current_state == desired_state:
        action = "checked" if activate else "unchecked"
        print(f"✓ '{checkbox.window_text()}' already {action}")
        return True


    # Toggle to desired state
    checkbox.toggle()
    action = "checked" if activate else "unchecked"
    print(f"✓ {action.capitalize()}: '{checkbox.window_text()}'")
    return True
