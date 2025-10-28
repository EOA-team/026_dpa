from pathlib import Path
import shutil
from pywinauto import Desktop, Application
import time

# Exclude Steps 05 and 06 because those steps will be done by this script
excluded_steps = ["05_output_parge",
                  "06_output_droacor", "06_output_droacor_final"]

# Set your Job
sel_folders = ["re112o_250903"]
raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")




def list_folders(path: Path) -> list:
    folders = [f.name for f in path.iterdir() if f.is_dir()]
    return folders


def copy_folder(origin: Path, dest: Path, folders: list, excluded_subfolder: list):
    print("Copying Started")
    for folder in folders:
        origin_folder = origin / folder
        dest_folder = dest / folder
        if not folder_exists(path=dest, folder=folder):
            print(f"Copying {folder} ...")
            shutil.copytree(str(origin_folder), str(dest_folder),
                            ignore=lambda src, names: [name for name in names if name in excluded_subfolder])
    print("Copying Finished")


def folder_exists(path: Path, folder: str) -> bool:
    existing_folders = list_folders(path)
    if folder in existing_folders:
        print(f"'{folder}' already exists!")
        return True
    return False


def main():
    copy_folder(origin=raw_folder, dest=process_folder,
                folders=sel_folders, excluded_subfolder=excluded_steps)
   
    '''  Approach does not work 
    app = Application(backend="uia").start("C:/ReSe_Software_Win/parge/PARGE.exe",
                                             work_dir= "C:/ReSe_Software_Win/parge/"  # Makes sure config.ini is loaded
                                             )
    dialog  = app['IDL Virtual Machine Application']
    btn_parge = dialog.child_window(title= "PARGE (64bit)", control_type = "Button")
    time.sleep(1)
    btn_parge.click_input()
    '''    
    app = Application(backend="uia").start(r"C:\ReSe_Software_Win\idl89\bin\bin.x86_64\idlrt.exe -vm=C:\ReSe_Software_Win\parge\parge.sav ")
    desktop = Desktop(backend="uia")
    #candidates = desktop.windows()
    #print(candidates)

    dlg = desktop.window(title='Runtime App')
    

    
    if dlg.exists():
        print("Found the Runtime App window")
        dlg.print_control_identifiers()
        pane = dlg.child_window(control_type="Pane")
        image = pane.child_window(auto_id="316", control_type="Image")
        image.click_input()  # real mouse click
    else:
        raise RuntimeError("Runtime App window not found")

    ''''
    app = Application(backend="win32").start(r"C:\ReSe_Software_Win\idl89\bin\bin.x86_64\idlrt.exe -vm=C:\ReSe_Software_Win\parge\parge.sav ")
    print(app.windows())
    dialog = app.window(title_re=".*Runtime.*")
    dialog.wait("visible ready", timeout=30)

    dialog.print_control_identifiers()
    '''

    

    



  

if __name__ == "__main__":
    main()
