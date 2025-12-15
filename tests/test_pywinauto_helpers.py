import pytest 
from code.pywinauto_helpers import (
    get_application, open_application,close_window_with_confirmation,
    handle_idl_vm_startup, find_control,
    DEFAULT_WAIT_TIME, Desktop
)

@pytest.fixture(scope="session")
def windows_desktop():
    print("\n🚀 Setting up Desktop for test session...")
    desktop = Desktop(backend="uia")
    
    yield desktop
    
    # Cleanup after all tests are done
    print("\n🧹 Cleaning up Desktop after test session...")


def test_find_control(windows_desktop):
    m4m_window = open_application(app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                     work_dir="C:/ReSe_Software_Win/m4mproc/",
                     idl_application=True, wait_time= DEFAULT_WAIT_TIME,
                     window_title="ReSe Hyspex Processor 2025", desktop=windows_desktop)
    # Find button using different methods
    select_exact = find_control(window=m4m_window, control_type="Button", control_name="Check Consistency", exact=True)
    select_partial = find_control(window=m4m_window, control_type="Button", control_name="check", exact=False)
    select_case = find_control(window=m4m_window, control_type="Button", control_name="check consistency", exact=True)  # lowercase
    
    # All should be found
    assert select_exact is not None, "Exact search failed"
    assert select_partial is not None, "Partial search failed"
    assert select_case is not None, "Case-insensitive search failed"
    
    # All should be the same button
    assert select_exact == select_partial == select_case, "Different search methods returned different buttons"
    
    # All should have same text
    assert select_exact.window_text() == select_partial.window_text() == select_case.window_text()
    
    # Find different button to verify they're not all the same
    process_btn = find_control(m4m_window, "Button", "Process", exact=True)
    assert process_btn is not None, "Could not find Process button"
    assert process_btn != select_exact, "Select and Process should be different buttons"
    
    print(f"✓ All tests passed! Found '{select_exact.window_text()}' and '{process_btn.window_text()}'")
    
    close_window_with_confirmation(m4m_window)

# def test_open_and_close_m4mproc(windows_desktop):
#     m4m= open_application(app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
#                      work_dir="C:/ReSe_Software_Win/m4mproc/",
#                      idl_application=True, wait_time= DEFAULT_WAIT_TIME,
#                      window_title="ReSe Hyspex Processor 2025", desktop=windows_desktop)
#     assert m4m.window_text() == "ReSe Hyspex Processor 2025"
#     m4m.close()
#     assert m4m.window_text() == None

    
    
