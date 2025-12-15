"""
PyWinAuto Helper Module

Common utility functions for Windows GUI automation using pywinauto.
Consolidates frequently used operations for window management, control finding,
and dialog handling.
"""

from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import TimeoutError
from pathlib import Path
from typing import Optional, List
import time 

# Default timeout for wait operations (seconds)
DEFAULT_WAIT_TIME = 5


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
    control_name: str,
    exact: bool = False,
    debug: bool = True
) -> Optional[UIAWrapper]:
    """
    Find a UI control by type and name.

        
    Examples:
        # Find button (partial match)
        btn = find_control(window, "Button", "Submit")
        
        # Find button (exact match)
        btn = find_control(window, "Button", "Submit", exact=True)
    """
    normalized_name = control_name.strip().lower()
    found_controls = []
    
    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type != control_type:
                continue
            
            control_text = ctrl.window_text().strip()
            found_controls.append(control_text)
            
            control_text_norm = control_text.lower()
            if exact:
                if normalized_name == control_text_norm:
                    return ctrl
            else:
                if normalized_name in control_text_norm:
                    return ctrl
                    
        except Exception:
            continue
    
    if debug:
        match_type = "exact" if exact else "partial"
        print(f"[DEBUG] Could not find {control_type} with name '{control_name}' ({match_type})")
        print(f"[DEBUG] Available {control_type} controls:")
        for ctrl_text in found_controls:
            print(f"  - '{ctrl_text}'")
    
    return None


def close_window_with_confirmation(window: UIAWrapper) -> bool:
    """
    Close window and press Enter to handle any confirmation.
    Simple and effective for most cases.
    """
    try:
        window.close()
        # Just press Enter - works for most confirmations
        window.type_keys("{ENTER}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False
        


def main():
    windows_desktop = Desktop(backend="uia")
    open_application(app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                     work_dir="C:/ReSe_Software_Win/m4mproc/",
                     idl_application=True, wait_time= DEFAULT_WAIT_TIME,
                     window_title="ReSe Hyspex Processor 2025", desktop=windows_desktop)
    



if __name__ == "__main__":
    main()

    
