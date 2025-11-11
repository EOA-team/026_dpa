import time
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings
from pathlib import Path
import shutil
from pyprojroot import here

Timings.Fast()
wait_time = 3



raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")



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
    
    def set_checkboxes(self):
        """
        Sets the checkboxes to match the desired state.
        Checks a box if desired_state is 1 and it's currently 0,
        unchecks a box if desired_state is 0 and it's currently 1.
        """
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

def file_exists(base_path: Path, filename: str) -> bool:
    return (base_path / filename).is_file()

def load_config_file(filepath: Path, window: UIAWrapper):
    if not filepath.is_file():
        print(f"Config File {filepath} does not exist...")
        src_file = here() / "code" /"configs" / filepath.name
        dst_file = filepath
        print(f"Copy from {src_file}")
        shutil.copy(src_file, dst_file)
    

        
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

    file_edit.type_keys(filepath)
    file_edit.type_keys("{ENTER}")



    

    











def main():
    # Create a Desktop Object to see all windows present on Desktop
    desktop = Desktop(backend="uia")

    m4m_window = get_m4mProc(desktop)
    checkboxes = CheckboxesControl(
        names= ["Raw Data Import", "Geocoding", "Reflectance Retrieval",
                "Topograhic and Radiometric Correction", "Product Generation", "Rectification", "Mosaic", "Point Cloud"],
        window=m4m_window,
        active=[ "Geocoding","Reflectance Retrieval","Rectification", "Mosaic" ]
    )
    load_config_file(filepath=process_folder / "conf_rese_prcsr.json", window=m4m_window)
    m4m_window.set_focus()
    m4m_window.click_input()
    checkboxes.set_checkboxes()
    





if __name__ == "__main__":
    main()
