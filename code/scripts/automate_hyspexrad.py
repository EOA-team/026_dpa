
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings, TimeoutError
from pathlib import Path

from code.pywinauto_helpers import open_application, find_control
from code.checkboxescontrol import CheckboxesControl
import time

Timings.fast()
wait_time = 5



raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")

sel_flights = ["re112o_250610", "re112o_250619","re112o_250717_2","re112o_250723_4",
               "re112o_250807", "re112o_250813", "re112o_250903", "re112o_250918"] # Relevant Flights for MT 


def get_hyspexrad(desktop: Desktop):
    tmp_window = desktop.window(title='HyspexRad_V3.5')
    if tmp_window.exists(timeout=wait_time):
        print("HyspexRad Window already exists!")
        window = tmp_window
    else:
        print("Window does not yet exist, will be created...")
        window= open_hyspexrad(desktop)
    
    return window


def open_hyspexrad(desktop: Desktop):
    # Launch Target Executable
    app = Application(backend="uia").start("G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe",
                                           work_dir="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/"
                                           )

    hyspexrad_window = desktop.window(title='HyspexRad_V3.5')
    hyspexrad_window.wait('exists', timeout=wait_time)

    # Bring window to foreground
    hyspexrad_window.set_focus()
    return hyspexrad_window


def find_element_by_title(window: UIAWrapper, element_type: str, title: str, partial: bool = True) -> UIAWrapper  :
    """
    Returns the first control within the given window
    that matches the specified title.

    Parameters:
    - window: UIAWrapper of the parent window.
    - element_type : "Button, RadioButton, ..."
    - title: Title of the element to search for.
    - partial: If True, allows partial (substring) matching.

    Returns:
    - UIAWrapper object representing the matching Button control,
      or None if no matching button is found.
    """
    normalized_title = title.strip().lower()
    found_elements = []

    for ctrl in window.descendants():
        try:
            if ctrl.element_info.control_type != element_type:
                continue

            element_text = ctrl.window_text().strip()
            found_elements.append(element_text)

            # check match
            element_text_norm = element_text.lower()
            if partial and normalized_title in element_text_norm:
                return ctrl
            elif not partial and normalized_title == element_text_norm:
                return ctrl

        except Exception:
            continue

def set_fileformat(window: UIAWrapper, fileformat: str):
    radio_button = find_control(window=window, control_type="RadioButton", control_name="bsq", exact=True)
    radio_button.select()        

def set_datatype(window: UIAWrapper, datatype: str):
    radio_button = find_control(window=window, control_type="RadioButton", control_name="32 bit float", exact=True)
    radio_button.select()   

  


        



def main():
    # Create a Desktop Object to see all windows present on Desktop
    windows_desktop = Desktop(backend="uia")
    hyspexrad_window = open_application(desktop=windows_desktop, 
                                  app_path="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe",
                                  work_dir="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/",
                                  idl_application=False,
                                  window_title="HyspexRad_V3.5")
    checkboxes = CheckboxesControl(window=hyspexrad_window)
    checkboxes.check("Radiance")
    checkboxes.uncheck("Reflectance")
    checkboxes.check("RGB")
    checkboxes.uncheck("Saturation Map")

    radio_button = find_control(window=hyspexrad_window, control_type="ListItem", control_name="JPG", exact=True)
    radio_button.select()   

    radio_button = find_control(window=hyspexrad_window, control_type="ListItem", control_name="ENVI Mask", exact=True)
    radio_button.select()   

    set_fileformat(window=hyspexrad_window, fileformat="bsq")
    set_datatype(window=hyspexrad_window, datatype="32 bit float")

    time.sleep(5)
    hyspexrad_window.close()



if __name__ == "__main__":
    main()

