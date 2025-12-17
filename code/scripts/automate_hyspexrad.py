
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings, TimeoutError
from pathlib import Path

from code.pywinauto_helpers import open_application, find_control, set_checkbox
from code.scripts.prepare_folders import folder_exists, get_nr_of_files, move_files_by_pattern
import time

Timings.fast()
wait_time = 5

NR_OF_SENSORS = 2 # VNIR , SWIR
FLIGHT_LINES = 3
OUTPUT_FILES_PER_FLIGHT_LINE = 3 # hdr , jpg, img

VNIR_TAG = "v1240"
SWIR_TAG = "s620"



raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")

sel_flights = ["re112o_250610", "re112o_250918"] # Relevant Flights for MT 


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

  
def set_output_folder(window: UIAWrapper,flight : str):
    editbox = find_control(window=window, control_type="Edit", found_index=0)
    editbox.set_edit_text(str(process_folder / flight / "tmp") + '\\')

def set_input_folder(window: UIAWrapper,flight : str):
    button  = find_control(window=window, control_type="Button", control_name="open images", exact=True)
    button.invoke()

    #File Selector
    image_selection_window = window.child_window(title='Select Images', control_type= "Window")
    image_selection_window.wait('exists', timeout=5)
    image_selection_window.set_focus()

    #Write Path 
    editbox = find_control(window=image_selection_window, control_type="Edit", control_name="file name:", exact=True, debug=True)
    editbox.set_edit_text(str(process_folder / flight / "RAW"))
    editbox.type_keys("{ENTER}")
    
    itemslist= find_control(window=image_selection_window, control_type="List", control_name="items view", exact=True, debug=True)
    itemslist.type_keys("^a")  # Ctrl+A
    

    open_btn = find_control(window=image_selection_window, control_type="Button", 
                            control_name="open", exact=True, found_index=2, debug=True)
    open_btn.click()
    
    


    # Wait for window to close
    image_selection_window.wait_not('exists', timeout=5)

def set_softwarebinning(window: UIAWrapper):
    swir_across_track = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=0)
    swir_across_track.select("1X")

    swir_spectral_direction = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=1)
    swir_spectral_direction.select("1X")

    swir_along_track = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=2)
    swir_along_track.select("1X")

    vnir_across_track = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=3)
    vnir_across_track.select("2X")

    vnir_spectral_direction = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=4)
    vnir_spectral_direction.select("2X")

    vnir_along_track = find_control(window=window, control_type="ComboBox", control_name="Software Binning", found_index=5)
    vnir_along_track.select("2X")

def set_output_fileformat(window: UIAWrapper, filerformat: str):
    combobox = find_control(window=window, control_type="ComboBox", 
                            control_name="Save", exact=True)
    combobox.select(filerformat)

def trigger_run(window: UIAWrapper):
    button = find_control(window=window, control_type="Button", control_name="run", exact=True)
    button.invoke()





def main():
    # Create a Desktop Object to see all windows present on Desktop
    windows_desktop = Desktop(backend="uia")
    hyspexrad_window = open_application(desktop=windows_desktop, 
                                  app_path="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe",
                                  work_dir="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/",
                                  idl_application=False,
                                  window_title="HyspexRad_V3.5")
    
    
    
    set_fileformat(window=hyspexrad_window, fileformat="bsq")
    set_datatype(window=hyspexrad_window, datatype="32 bit float")
    set_output_fileformat(window=hyspexrad_window, filerformat="JPG")

    set_checkbox(window=hyspexrad_window, checkbox_name="radiance" ,activate=True, exact=True)
    set_checkbox(window=hyspexrad_window, checkbox_name="reflectance" ,activate=False, exact=True)
    set_checkbox(window=hyspexrad_window, checkbox_name="rgb" ,activate=True, exact=True)
    set_checkbox(window=hyspexrad_window, checkbox_name="saturation map" ,activate=False, exact=True)


    for flight in sel_flights:
        # Create tmp folder for this flight
        tmp_folder = process_folder / flight / "tmp"
        tmp_folder.mkdir(parents=True, exist_ok=True)

        

   
        
        set_output_folder(window=hyspexrad_window, flight=flight)
        set_input_folder(window=hyspexrad_window, flight=flight)
        set_softwarebinning(window=hyspexrad_window)
        trigger_run(window=hyspexrad_window)
        
        nr_files = 0
        expected_files = NR_OF_SENSORS * FLIGHT_LINES * OUTPUT_FILES_PER_FLIGHT_LINE
        
        while nr_files != expected_files:
            nr_jpg = get_nr_of_files(base_path=tmp_folder, pattern="*.JPG")
            nr_hdr = get_nr_of_files(base_path=tmp_folder, pattern="*.hdr")
            nr_img = get_nr_of_files(base_path=tmp_folder, pattern="*.img")
            nr_files = nr_jpg + nr_hdr + nr_img
            print(f"Files found: {nr_files}/{expected_files} (jpg:{nr_jpg}, hdr:{nr_hdr}, img:{nr_img})")
            time.sleep(1)
        
        swir_folder = process_folder / flight / "SWIR"
        move_files_by_pattern(source=tmp_folder, destination=swir_folder, pattern=SWIR_TAG)

        vnir_folder = process_folder / flight / "VNIR"
        move_files_by_pattern(source=tmp_folder, destination=vnir_folder, pattern=VNIR_TAG)


    hyspexrad_window.close()



if __name__ == "__main__":
    main()

