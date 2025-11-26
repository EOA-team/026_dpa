
from pywinauto import Desktop, Application
from pywinauto.timings import Timings
import time

Timings.Defaults()


'''How to use Pywinauto

See Windows and Control Identifiers
<your_element>.print_control_identifiers()
<your_desktop>.windows()

Very important to make sure control identifiers are shown 
idlvm_window.wait('exists', timeout=1)



'''


def main():

    wait_time = 10

    # Launch Target Executable
    app = Application(backend="uia").start("C:/ReSe_Software_Win/parge/PARGE.exe",
                                            work_dir="C:/ReSe_Software_Win/parge/"  # Makes sure config.ini is loaded
                                            )

    #Alternative: 
    #app = Application(backend="win32").start(r"C:\ReSe_Software_Win\idl89\bin\bin.x86_64\idlrt.exe -vm=C:\ReSe_Software_Win\parge\parge.sav ")

    # Create a Desktop Object to see all 
    desktop = Desktop(backend="uia")


    idlvm_window = desktop.window(title='Runtime App')
    idlvm_window.wait('exists', timeout=wait_time)
    pane = idlvm_window.child_window(control_type="Pane")
    pane.wait('exists', timeout=wait_time)
    image = pane.child_window(auto_id="316", control_type="Image")
    image.wait('exists', timeout=wait_time)
    image.click_input()

    #Control Parge 
    parge_window = desktop.window(title='P A R G E  Parametric Orthorectification')
    parge_window.wait('exists', timeout=wait_time) 
    
    
    parge_window.wrapper_object().set_focus()
    time.sleep(1)



    menu_bar = parge_window.child_window(title="Application", control_type="MenuBar")
    menu_bar.wait('exists', timeout=wait_time)


    #Make sure DSM Menu is openede
    dsm_tab = menu_bar.child_window(title="DSM", control_type="MenuItem")
    dsm_tab.wait('exists', timeout=wait_time)
    dsm_tab.expand()
    time.sleep(3)

    # Make sure Import Menu is opened 
    dsm_menu = parge_window.child_window(title = "DSM", control_type = "Menu")
    import_sel = dsm_menu.child_window(title = "Import", control_type= "MenuItem")
    import_sel.wait('exists', timeout=wait_time)
    import_sel.click_input()

    import_menu = parge_window.child_window(title = "Import", control_type = "Menu")
    geotiff_sel = import_menu.child_window(title = "GEOTIFF", control_type= "MenuItem")
    geotiff_sel.wait('exists', timeout=wait_time)
    geotiff_sel.click_input()
    time.sleep(3)

    #Now Geotiff Window Opens
    read_geotiff_window = desktop.window(title='Read GEOTIFF DEM')
    read_geotiff_window.wait('exists', timeout=wait_time) 
    read_geotiff_window.print_control_identifiers()

    #Access the ComboBox
    file_combo = read_geotiff_window.child_window(title="File name:", control_type="ComboBox")
    file_combo.wait('exists', timeout=wait_time) 

    #Write Path 
    file_edit = file_combo.child_window(control_type="Edit")
    file_edit.wait('exists', timeout=wait_time) 
    file_edit.click_input()  # make sure focus is on the edit
    file_edit.type_keys(r"E:\mjolnir_processing\re112o_250903\02_dsm\dem.tif{ENTER}", with_spaces=True)

    open_button = file_combo.child_window(title="Open", control_type="Button")
    open_button.wait('exists', timeout=wait_time) 
    open_button.click_input()


if __name__ == "__main__":
    
    main()
