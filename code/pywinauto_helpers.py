"""
PyWinAuto Helper Module

Common utility functions for Windows GUI automation using pywinauto.
Consolidates frequently used operations for window management, control finding,
and dialog handling.
"""

from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from typing import Optional, List
import time

# Default timeout for wait operations (seconds)
DEFAULT_WAIT_TIME = 3


def get_application(
    desktop: Desktop,
    window_title: str,
    wait_time: int = DEFAULT_WAIT_TIME
) -> Optional[UIAWrapper]:
    tmp_window = desktop.window(title=window_title)
    if tmp_window.exists(timeout=wait_time):
        print(f"Window '{window_title}' already exists!")
        return tmp_window
    else:
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
    work_dir: Optional[str] = None,
    idl_application: bool = False,
    wait_time: int = DEFAULT_WAIT_TIME
) -> UIAWrapper:
    # First check if application already exists
    existing_window = get_application(desktop, window_title, wait_time)
    if existing_window:
        return existing_window
    else:
        print(f"Opening application: {app_path}")
        app = Application(backend="uia").start(app_path, work_dir=work_dir)
        # Handle IDL VM startup if needed
        if idl_application:
            handle_idl_vm_startup(desktop, wait_time)
        window = desktop.window(title=window_title)
        window.wait('exists', timeout=wait_time)
        window.set_focus()
        print(f"✓ Application '{window_title}' opened successfully")
        return window
def find_control(
    window: UIAWrapper,
    control_type: str,
    control_name: str = "",
    exact: bool = False,
    found_index: Optional[int] = None,
    debug: bool = True
) -> Optional[UIAWrapper]:
    """
    Find a UI control by type and name.
    Examples:
        # Find button (partial match)
        btn = find_control(window, "Button", "Submit")
        
        # Find button (exact match)
        btn = find_control(window, "Button", "Submit", exact=True)

        # Find second ComboBox named "Save"
        combo = find_control(window, "ComboBox", "Save", exact=True, found_index=1)
        
        # Find second ListBox (any name)
        listbox = find_control(window, "ListBox", found_index=1)
    """
    # Bring window to foreground to ensure controls are accessible
    window.set_focus()

    normalized_name = control_name.strip().lower()
    found_controls = []
    matching_controls = []

    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type != control_type:
                continue

            control_text = ctrl.window_text().strip()
            found_controls.append(control_text)
            # Check if name matches (if control_name is provided)
            name_matches = True
            if control_name:
                control_text_norm = control_text.lower()
                if exact:
                    name_matches = (normalized_name == control_text_norm)
                else:
                    name_matches = (normalized_name in control_text_norm)
            # If found_index is specified, collect matching controls
            if found_index is not None:
                if name_matches:  # Only collect if name matches (or no name specified)
                    matching_controls.append(ctrl)
                continue
            # If no found_index, return first match
            if control_name and name_matches:
                return ctrl
        except Exception:
            continue
    # If found_index was specified, return the control at that index
    if found_index is not None:
        if 0 <= found_index < len(matching_controls):
            return matching_controls[found_index]
        elif debug:
            name_info = f" with name '{control_name}'" if control_name else ""
            print(f"[DEBUG] Could not find {control_type}{name_info} at index {found_index}")
            print(f"[DEBUG] Found {len(matching_controls)} matching {control_type} controls (indices 0-{len(matching_controls)-1})")
        return None

    if debug:
        match_type = "exact" if exact else "partial"
        print(f"[DEBUG] Could not find {control_type} with name '{control_name}' ({match_type})")
        print(f"[DEBUG] Available {control_type} controls:")
        for ctrl_text in found_controls:
            print(f"  - '{ctrl_text}'")

    return None

def find_controls_by_type(
    window: UIAWrapper,
    control_type: str,
    debug: bool = True
) -> List[UIAWrapper]:
    """
    Find ALL controls of a specific type.
    
    Examples:
        # Find all buttons
        buttons = find_controls(window, "Button")
        
        # Find all checkboxes
        checkboxes = find_controls(window, "CheckBox")
    """
    # Bring window to foreground to ensure controls are accessible
    window.set_focus()

    found_controls = []

    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type != control_type:
                continue

            found_controls.append(ctrl)

        except Exception:
            continue

    if debug:
        print(f"[DEBUG] Found {len(found_controls)} {control_type} controls")
        for ctrl in found_controls:
            try:
                name = ctrl.window_text().strip()
                print(f"  - '{name}'")
            except:
                print("  - (unnamed)")

    return found_controls

def close_window_with_confirmation(
    window: UIAWrapper,
    desktop: Desktop,
    confirmation_buttons: list[str],
    wait_for_dialog: int = DEFAULT_WAIT_TIME
) -> bool:
    """
    Close a window and automatically handle confirmation dialog if it appears.
    Also works for windows that close immediately without confirmation.

        
    Examples:
        # Must specify which button(s) to click
        close_window_with_confirmation(window, desktop, confirmation_buttons=["Yes"])
        
        # Try multiple buttons in order
        close_window_with_confirmation(window, desktop, confirmation_buttons=["Don't Save", "No", "OK"])
        
        # Custom wait time
        close_window_with_confirmation(window, desktop, confirmation_buttons=["Yes"], wait_for_dialog=2.0)
    """

    # Bring window to foreground to ensure controls are accessible
    window.set_focus()

    # Validate that confirmation_buttons is provided and not empty
    if not confirmation_buttons:
        raise ValueError("confirmation_buttons must be provided and cannot be empty. "
                        "Example: confirmation_buttons=['Yes'] or ['OK', 'No']")

    try:
        window.set_focus()
        # Attempt to close the window
        print(f"Closing window: '{window.window_text()}'")
        window.close()

        # Small initial wait to see if window closes immediately
        time.sleep(0.3)

        # Check if window closed without confirmation
        if not window.exists():
            print("  ✓ Window closed immediately (no confirmation needed)")
            return True

        # Window still exists, wait for potential confirmation dialog
        time.sleep(wait_for_dialog - 0.3)

        # Look for confirmation dialogs
        dialog_handled = False
        for ctrl in desktop.windows():
            try:
                # Check if it's a visible dialog
                if not ctrl.is_visible():
                    continue

                # Check if it's a dialog window
                class_name = ctrl.class_name() if hasattr(ctrl, 'class_name') else ''
                if not (ctrl.is_dialog() or
                       class_name in ["#32770", "Dialog", "Window"] or
                       "dialog" in ctrl.window_text().lower()):
                    continue

                print(f"  Found dialog: '{ctrl.window_text()}'")

                # Try each confirmation button using find_control
                for btn_name in confirmation_buttons:
                    try:
                        btn = find_control(
                            window=ctrl,
                            control_type="Button",
                            control_name=btn_name,
                            exact=False,
                            debug=False
                        )

                        if btn and btn.is_visible() and btn.is_enabled():
                            print(f"  Clicking '{btn.window_text()}' button...")
                            btn.click()
                            time.sleep(0.5)
                            dialog_handled = True
                            break
                    except Exception:
                        continue

                if dialog_handled:
                    break

            except Exception:
                continue

        if dialog_handled:
            print("  ✓ Confirmation dialog handled")

        # Check if window closed successfully
        time.sleep(0.5)
        if not window.exists():
            print("  ✓ Window closed successfully")
            return True
        else:
            print("  ⚠️ Window still exists after close attempt")
            return False

    except Exception as e:
        print(f"  ⚠️ Error closing window: {e}")
        return False

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
    checkbox = find_control(window, "CheckBox", checkbox_name, exact=exact, debug=False)

    if not checkbox:
        print(f"⚠️ Checkbox not found: '{checkbox_name}'")
        return False

    try:
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

    except Exception as e:
        print(f"⚠️ Error setting checkbox '{checkbox_name}': {e}")
        return False

def main():
    pass


if __name__ == "__main__":
    main()


