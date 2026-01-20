import pytest 
import time
from code.pywinauto_helpers_new import (
    ApplicationManager, DesktopManager,
    ControlFinder, ControlNotFoundError
)


def test_context_manager():
    with ApplicationManager( app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                             work_dir="C:/ReSe_Software_Win/m4mproc/",
                             window_title="ReSe Hyspex Processor 2025",
                             is_idl_application=True) as rese_manager:



        assert rese_manager.app.is_process_running()

    assert not rese_manager.app.is_process_running()

def test_control_finder():
    with ApplicationManager( app_path="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe",
                             work_dir="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/",
                             window_title="HyspexRad_V3.5",
                             is_idl_application=False) as hyspexrad_manager:
        
        controlfinder = ControlFinder(window=hyspexrad_manager.window)

        # Find checkbox by AutomationId
        checkbox_autoid = controlfinder.find_by_auto_id(control_type= "CheckBox", auto_id="Widget.rightsideGroupBox.reflectanceCheckBox")
        # Find checkbox by Name 
        checkbox_name = controlfinder.find_by_type_and_name(control_type="CheckBox", control_name="reflectance", exact=True)
        assert checkbox_autoid == checkbox_name

    
    

    

