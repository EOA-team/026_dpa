import pytest 
from code.pywinauto_helpers import (
    open_application,close_window_with_confirmation,
    find_control,set_checkbox,
    DEFAULT_WAIT_TIME, Desktop
)


@pytest.fixture(scope="session")
def windows_desktop():
    print("\n🚀 Setting up Desktop for test session...")
    desktop = Desktop(backend="uia")
    
    yield desktop
    
    # Cleanup after all tests are done
    print("\n🧹 Cleaning up Desktop after test session...")

def test_open_application_only_once_simple(windows_desktop):
    """Test that open_application reuses existing window."""
    
    # First call
    window1 = open_application(
        desktop=windows_desktop,
        app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
        work_dir="C:/ReSe_Software_Win/m4mproc/",
        window_title="ReSe Hyspex Processor 2025",
        idl_application=True
    )
    
    assert window1 is not None
    assert window1.exists()
    handle1 = window1.handle
    
    # Second call - should return same window
    window2 = open_application(
        desktop=windows_desktop,
        app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
        work_dir="C:/ReSe_Software_Win/m4mproc/",
        window_title="ReSe Hyspex Processor 2025",
        idl_application=True
    )
    
    # Compare by window handle, not object identity
    handle2 = window2.handle
    assert handle1 == handle2, f"Different windows! {handle1} vs {handle2}"
    
    # Third call
    window3 = open_application(
        desktop=windows_desktop,
        app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
        work_dir="C:/ReSe_Software_Win/m4mproc/",
        window_title="ReSe Hyspex Processor 2025",
        idl_application=True
    )
    
    handle3 = window3.handle
    assert handle3 == handle1, f"Third call different! {handle3} vs {handle1}"
    
    print(f"✓ All calls returned same window (handle: {handle1})")


def test_open_and_close(windows_desktop):
    m4m_window= open_application(app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                     work_dir="C:/ReSe_Software_Win/m4mproc/",
                     idl_application=True, wait_time= DEFAULT_WAIT_TIME,
                     window_title="ReSe Hyspex Processor 2025", desktop=windows_desktop)
    assert m4m_window.window_text() == "ReSe Hyspex Processor 2025"
    close_window_with_confirmation(desktop=windows_desktop,
                                   window=m4m_window,
                                   confirmation_buttons=["Yes"])

     # Check window is closed
    assert not m4m_window.exists(), "Window still exists"
    print("✓ Window closed successfully")





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
    
    close_window_with_confirmation(desktop=windows_desktop,
                                   window=m4m_window,
                                   confirmation_buttons=["Yes"])
    


def test_controls_fail_on_minimized_window(windows_desktop):


    m4m_window = open_application(app_path="C:/ReSe_Software_Win/m4mproc/M4Mproc.exe",
                     work_dir="C:/ReSe_Software_Win/m4mproc/",
                     idl_application=True, wait_time= DEFAULT_WAIT_TIME,
                     window_title="ReSe Hyspex Processor 2025", desktop=windows_desktop)
    

    
    m4m_window.minimize()

    help_menu = find_control(window=m4m_window, control_type="MenuItem", control_name="help", exact=True)
    assert help_menu is not None, "Help menu not found"
    print("✓ Found Help menu")
    help_menu.select()
    print("✓ Select worked (window is focused)")


    m4m_window.minimize()
    print("\nAttempting to select() on minimized window (should fail)...")

    with pytest.raises(Exception) as exc_info:
        help_menu.select()

    print(f"✓ Expected error: {type(exc_info.value).__name__}: {exc_info.value}")
    print("✓ Confirmed: Cannot interact with controls when window is minimized")

    close_window_with_confirmation(desktop=windows_desktop,
                                   window=m4m_window,
                                   confirmation_buttons=["Yes"])



def test_set_checkbox(windows_desktop):
    """Test checking and unchecking a checkbox."""
    
    # Open HyspexRad
    hyspexrad_window = open_application(
        desktop=windows_desktop,
        app_path="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe",
        work_dir="G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/",
        window_title="HyspexRad_V3.5",
        idl_application=False
    )
    
    print("\n=== Test 1: Check initial state ===")
    checkbox = find_control(
        window=hyspexrad_window,  
        control_type="CheckBox",
        control_name="radiance",
        exact=True, 
        debug=False
    )
    
    assert checkbox is not None, "Radiance checkbox not found"
    
    state = checkbox.get_toggle_state()
    print(f"Initial state: {state} (1=checked, 0=unchecked)")
    
    assert state == 1, "Expected Radiance to be checked by default"
    print("✓ Radiance is checked by default")
    
    # Test 2: Uncheck the checkbox
    print("\n=== Test 2: Uncheck checkbox ===")
    result = set_checkbox(
        window=hyspexrad_window,  
        checkbox_name="radiance",
        activate=False,
        exact=True
    )
    
    assert result, "Failed to uncheck checkbox"
    
    # Verify it's unchecked
    checkbox = find_control(
        window=hyspexrad_window,
        control_type="CheckBox",
        control_name="radiance",
        exact=False,
        debug=True
    )
    
    state = checkbox.get_toggle_state()
    assert state == 0, "Expected Radiance to be unchecked"
    print("✓ Radiance is now unchecked")
    
    # Test 3: Check the checkbox again
    print("\n=== Test 3: Check checkbox again ===")
    result = set_checkbox(
        window=hyspexrad_window,
        checkbox_name="radiance",
        activate=True,
        exact=True
    )
    
    assert result, "Failed to check checkbox"
    
    # Verify it's checked
    checkbox = find_control(
        window=hyspexrad_window,
        control_type="CheckBox",
        control_name="radiance",
        exact=False,
        debug=False
    )
    
    state = checkbox.get_toggle_state()
    assert state == 1, "Expected Radiance to be checked again"  # Fixed: should be 1, not 0
    print("✓ Radiance is checked again")
    
    # Cleanup
    print("\n=== Cleanup ===")
    close_window_with_confirmation(
        hyspexrad_window,
        windows_desktop,
        confirmation_buttons=["Yes", "OK"]
    )
    
    print("\n✓✓✓ All tests passed!")
    
        
        
    
    
