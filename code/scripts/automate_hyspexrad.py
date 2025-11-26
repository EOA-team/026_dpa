
from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import Timings, TimeoutError
from pathlib import Path

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
    app = Application(backend="uia").start("G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe")

    hyspexrad_window = desktop.window(title='HyspexRad_V3.5')
    hyspexrad_window.wait('exists', timeout=wait_time)

    # Bring window to foreground
    hyspexrad_window.set_focus()
    return hyspexrad_window



def main():
    # Create a Desktop Object to see all windows present on Desktop
    desktop = Desktop(backend="uia")

    m4m_window = get_hyspexrad(desktop)



if __name__ == "__main__":
    main()

