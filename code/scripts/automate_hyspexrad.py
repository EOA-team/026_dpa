
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings, TimeoutError
from pathlib import Path

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




def main():
    # Create a Desktop Object to see all windows present on Desktop
    desktop = Desktop(backend="uia")
    m4m_window = get_hyspexrad(desktop)
    
    m4m_window.print_control_identifiers()
    
    rb1 = find_element_by_title(window=m4m_window, element_type="RadioButton", partial=True, title="BSQ")
    rb1.select()


    rb2 = find_element_by_title(window=m4m_window, element_type="RadioButton", partial=True, title="32 bit float")
    rb2.select()


    rb3 = find_element_by_title(window=m4m_window, element_type="CheckBox", partial=True, title="radiance ")
    rb3.invoke()


    rb4 = find_element_by_title(window=m4m_window, element_type="CheckBox", partial=True, title="rgb")
    rb4.invoke()

    rb5 = find_element_by_title(window=m4m_window, element_type="ListItem", partial=True, title="JPG")
    rb5.select()

    rb5 = find_element_by_title(window=m4m_window, element_type="ListItem", partial=True, title="Envi Mask ")
    rb5.select()


    time.sleep(5)
    m4m_window.close()



if __name__ == "__main__":
    main()

