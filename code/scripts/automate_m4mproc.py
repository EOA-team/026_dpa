import time
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings, TimeoutError
from pathlib import Path
import shutil
from pyprojroot import here

Timings.fast()
wait_time = 5



raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")

sel_flights = ["re112o_250610", "re112o_250619","re112o_250717_2","re112o_250723_4",
               "re112o_250807", "re112o_250813", "re112o_250903", "re112o_250918"] # Relevant Flights for MT 


activate_processes = [ "Geocoding","Reflectance Retrieval","Rectification", "Mosaic" ]



class CheckboxesControl:
    def __init__(self, window: UIAWrapper, names: list[str], active : list[str]):
        self.window = window
        self.names = names  
        self.checkboxes = self.find_checkboxes() 
        self.state = self.get_active_states()
        self.desired_state = self.get_desired_state(active)

    def find_checkboxes(self) -> list[UIAWrapper]:
        """
        Returns a list of all checkable controls (checkboxes).
        Handles both CheckBox controls and Buttons with TogglePattern.

        Returns:
        - List of pywinauto UIAWrapper objects representing checkboxes
        """
        checkboxes: list[UIAWrapper] = []

        for ctrl in self.window.descendants():
            try:
                # If control is CheckBox OR supports TogglePattern (UIA buttons that act as checkboxes)
                if ctrl.element_info.control_type == "CheckBox":
                    checkboxes.append(ctrl)
                else:
                    # Some Buttons act as checkboxes; check if it has TogglePattern
                    if ctrl.get_toggle_pattern() is not None:
                        checkboxes.append(ctrl)
            except Exception:
                # Some controls may not support TogglePattern; skip them
                continue

        return checkboxes
    
    def get_active_states(self) -> list[int]:
        """
        Returns a list of 0/1 representing the current checked state
        of each checkbox in the list.

        0 = unchecked
        1 = checked
        """
        states = []
        for cb in self.checkboxes:
            try:
                state = cb.get_toggle_state()  # 0=Off, 1=On, 2=Indeterminate
                states.append(1 if state == 1 else 0)
            except Exception as e:
                print(f"⚠️ Could not read state of '{cb.window_text()}': {e}")
                states.append(None)  # use None if state cannot be read
        return states
    
    def get_desired_state(self, active_names):
        state = [1 if word in active_names else 0 for word in self.names]
        return state
    
    def focus_window(self):
        self.window.set_focus()
        self.window.click_input()
    
    def set_checkboxes(self):
        """
        Sets the checkboxes to match the desired state.
        Checks a box if desired_state is 1 and it's currently 0,
        unchecks a box if desired_state is 0 and it's currently 1.
        """
        self.focus_window()
        for cb, current, desired in zip(self.checkboxes, self.state, self.desired_state):
            try:
                if current is None:
                    continue  # Skip checkboxes whose state couldn't be read
                if current != desired:
                    cb.toggle()  # Toggle changes state from checked<->unchecked
            except Exception as e:
                print(f"⚠️ Could not set state of '{cb.window_text()}': {e}")

        # Update the internal state after setting
        self.state = self.get_active_states()


def open_idlvm(desktop: Desktop):
    idlvm_window = desktop.window(title='Runtime App')
    idlvm_window.wait('exists', timeout=wait_time)
    return idlvm_window

def get_m4mProc(desktop: Desktop):
    tmp_window = Desktop(backend="uia").window(title='ReSe Hyspex Processor 2025')
    if tmp_window.exists(timeout=wait_time):
        print("M4M Window already exists!")
        window = tmp_window
    else:
        print("Window does not yet exist, will be created...")
        window= open_M4MProc(desktop)
    
    return window


def open_M4MProc(desktop: Desktop):
    # Launch Target Executable
    app = Application(backend="uia").start("C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                                           work_dir="C:/ReSe_Software_Win/m4mproc/"  # Makes sure config.ini is loaded
                                           )
    
    idlvm_window = open_idlvm(desktop)
    pane = idlvm_window.child_window(control_type="Pane")
    pane.wait('exists', timeout=wait_time)
    image = pane.child_window(auto_id="316", control_type="Image")
    image.wait('exists', timeout=wait_time)
    image.click_input()

    m4m_window = desktop.window(title='ReSe Hyspex Processor 2025')
    m4m_window.wait('exists', timeout=wait_time)

    # Bring window to foreground
    m4m_window.set_focus()
    m4m_window.click_input()
    return m4m_window

def file_exists(base_path: Path, pattern: str) -> bool:
    """
    Check if any file matching the pattern exists in the folder.

    Args:
        base_path (Path): Folder to search in.
        pattern (str): Filename or glob pattern, e.g., '*.bsq'.

    Returns:
        bool: True if at least one matching file exists, False otherwise.
    """
    if not base_path.is_dir():
        return False 

    # Use glob to match patterns like *.bsq or specific names
    matching_files = list(base_path.glob(pattern))
    return len(matching_files) > 0

def load_config_file(filepath: Path, window: UIAWrapper):
    if not filepath.is_file():
        print(f"Config File {filepath} does not exist...")
        src_file = here() / "code" /"configs" / filepath.name
        dst_file = filepath
        print(f"Copy from {src_file}")
        shutil.copy(src_file, dst_file)
    
    #Focus Window
    window.set_focus()
    window.click_input()
        
    #Expand  Edit Tab 
    menu_bar = window.child_window(title="Application", control_type="MenuBar")
    menu_bar.wait('exists', timeout=wait_time)
    edit_tab = menu_bar.child_window(title="Edit", control_type="MenuItem")
    edit_tab.wait('exists', timeout=wait_time)
    edit_tab.expand()

    # Open File Selector
    edit_menu = window.child_window(title = "Edit", control_type = "Menu")
    load_config = edit_menu.child_window(title = "Load Configuration", control_type= "MenuItem")
    load_config.wait('exists', timeout=wait_time)
    load_config.click_input()
    
    #File Selector
    filesel_dialog = window.child_window(title='Please Select a File', control_type= "Window")

    filesel_dialog.wait('exists', timeout=wait_time) 
    filesel_dialog.set_focus()
    filesel_dialog.click_input()

     #Access the ComboBox
    file_combo = filesel_dialog.child_window(title="File name:", control_type="ComboBox")
    file_combo.wait('exists', timeout=wait_time) 

    #Write Path 
    file_edit = file_combo.child_window(control_type="Edit")
    file_edit.wait('exists', timeout=wait_time) 
    # make sure focus is on the edit
    file_edit.set_focus()
    file_edit.click_input()  

    file_edit.set_edit_text(filepath)
    file_edit.type_keys("{ENTER}")


def close_window(window: UIAWrapper):
    window.close()
    ctrl_window = window.child_window(title='IDL Control Window', control_type= "Window")
    ctrl_window.wait('exists', timeout=wait_time) 
    ctrl_window.type_keys("{ENTER}")


def initialize_m4mProc(window : UIAWrapper):
    checkboxes = CheckboxesControl(
        names= ["Raw Data Import", "Geocoding", "Reflectance Retrieval",
                "Topograhic and Radiometric Correction", "Product Generation", "Rectification", "Mosaic", "Point Cloud"],
        window=window,
        active= activate_processes
    )
    load_config_file(filepath=process_folder / "conf_rese_prcsr.json", window=window)
    checkboxes.set_checkboxes()

def find_editboxes(window: UIAWrapper) -> list[UIAWrapper]:
    """
    Returns a list of all Edit controls within the given window.

    Parameters:
    - window: UIAWrapper of the parent window.

    Returns:
    - List of UIAWrapper objects representing Edit controls.
    """
    edit_controls: list[UIAWrapper] = []

    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type == "Edit":
                edit_controls.append(ctrl)
        except Exception:
            # Skip controls that can't be accessed
            continue

    return edit_controls

def find_button_by_title(window: UIAWrapper, title: str, partial: bool = True) -> UIAWrapper:
    """
    Returns the first Button control within the given window
    that matches the specified title.

    Parameters:
    - window: UIAWrapper of the parent window.
    - title: Title of the button to search for.
    - partial: If True, allows partial (substring) matching.

    Returns:
    - UIAWrapper object representing the matching Button control,
      or None if no matching button is found.
    """
    normalized_title = title.strip().lower()
    found_buttons = []

    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type != "Button":
                continue

            btn_text = ctrl.window_text().strip()
            found_buttons.append(btn_text)

            # check match
            btn_text_norm = btn_text.lower()
            if partial and normalized_title in btn_text_norm:
                return ctrl
            elif not partial and normalized_title == btn_text_norm:
                return ctrl

        except Exception:
            continue

    # If no button found, print all available button names for debugging
    print(f"[DEBUG] Could not find button with title '{title}'. Available buttons:")
    for btn_name in found_buttons:
        print(f" - '{btn_name}'")

    return None



def start_process(window: UIAWrapper):
    process_btn = find_button_by_title(window, title = " Process " )
    process_btn.invoke()

def confirm_alert(window: UIAWrapper):
    try:
        # Try to find and wait for the alert window
        alert_window = window.child_window(title='IDL Alert Window', control_type="Window")
        alert_window.wait('exists', timeout=wait_time)

        # Try to find the OK button
        ok_btn = find_button_by_title(window, title='OK')  # Spaces important!
        ok_btn.invoke()
        print(f"⚠️ 'IDL Alert Window' appeared  — Skipping this flight ")

    except TimeoutError:
        print(f"⚠️ 'IDL Alert Window' did not appear  — There must be another issue ")
   


def confirm_control(window: UIAWrapper) -> bool:
    try:
        # Try to find and wait for the control window
        ctrl_window = window.child_window(title='IDL Control Window', control_type="Window")
        ctrl_window.wait('exists', timeout=wait_time)

        # Try to find the OK button
        ok_btn = find_button_by_title(window, title='  OK  ')  # Spaces important!
        ok_btn.invoke()
        return (True)

    except TimeoutError:
        confirm_alert(window=window)
        return False

def trigger_close_console(desktop: Desktop):
    proc_console = desktop.window(title='M4M Processor Console')
    proc_console.wait('exists', timeout=wait_time)
    done_btn = find_button_by_title(proc_console, title = ' Done ' ) # Spaces important: otherwise cannot find btn
    done_btn.invoke() # Trigger that Processor Console Closes as soon as it is finished

def wait_until_process_finished(flight : str ):
    # Wait until there is a bsq and hdr file in the output 
    while True:
        bsq_exists = file_exists(base_path=process_folder/ flight / "output" / "mosaics" , pattern= "*.bsq" ) 
        hdf_exists = file_exists(base_path=process_folder/ flight / "output" / "mosaics" , pattern= "*.hdr" ) 
        if bsq_exists and hdf_exists :
            break



def set_foldepaths(folder_editboxes: list[UIAWrapper], flight : str):
    for editbox in folder_editboxes:
        name = editbox.element_info.name.strip()
        if(name == "Main Input Directory:"):
            editbox.set_edit_text(str(process_folder / flight) + '\\') # The '\' is important otherwise SWIR and VNIR are not found'
        elif(name == "DSM File:"):
            editbox.set_edit_text(str(process_folder / flight / "DSM" /"DSM"))
        elif(name == "Output directory:"):
            editbox.set_edit_text(str(process_folder / flight / "output") + '\\') # The '\' is important otherwise out dir not created

    
def main():
    # Create a Desktop Object to see all windows present on Desktop
    desktop = Desktop(backend="uia")

    m4m_window = get_m4mProc(desktop)
    editboxes = find_editboxes(window=m4m_window)
    for flight in sel_flights:
        initialize_m4mProc(window=m4m_window) # Make sure defaults are loaded after each loop --> Resets MOSDIR
        print(f"Processing {flight}🛠️...")
        set_foldepaths(flight = flight, folder_editboxes=editboxes )
        start_process(window=m4m_window)
        if confirm_control(window=m4m_window):
            trigger_close_console(desktop)
            wait_until_process_finished(flight=flight)
            print("Finished✅")
       
    
    #close_window(window=m4m_window)
    
    





if __name__ == "__main__":
    main()
