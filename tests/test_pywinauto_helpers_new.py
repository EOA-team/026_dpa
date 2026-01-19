import pytest 
import time
from code.pywinauto_helpers_new import (
    ApplicationManager, DesktopManager
)


def test_context_manager():
    with ApplicationManager( app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                             work_dir="C:/ReSe_Software_Win/m4mproc/",
                             window_title="ReSe Hyspex Processor 2025",
                             is_idl_application=True) as rese_manager:
        assert rese_manager.app.is_process_running()

    assert not rese_manager.app.is_process_running() 
    
    

    

