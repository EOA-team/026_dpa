from pywinauto.application import Application
import time
print("start")
app = Application(backend = "uia").start(r"C:\Program Files\Applanix\POSPac UAV 9.3\POSPacUAV.exe")

dialogs  = app['PosPac UAV']

ribbon_tabs = dialogs.child_window(title="Ribbon Tabs", auto_id="Ribbon Tabs", control_type="Pane")
proj_tab = ribbon_tabs.child_window(title="Project", control_type="TabItem")
edit_tab = ribbon_tabs.child_window(title="Edit", control_type="TabItem")
btn_close = dialogs.child_window(title= "Close", control_type = "Button")

edit_tab.click_input()
time.sleep(1)
proj_tab.click_input()
time.sleep(1)
edit_tab.click_input()
time.sleep(1)
proj_tab.click_input()
time.sleep(1)
btn_close.click_input()
print("finsihed")

