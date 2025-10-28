from pathlib import Path
import shutil

# Set your Job
sel_folders = ["re112o_250903"]
raw_folder = Path("D:/data/mjolnir")
excluded_steps = ["05_output_parge", "06_output_droacor", "06_output_droacor_final"] 
process_folder = Path("E:/mjolnir_processing")





def list_folders(dir: Path) -> list:
    folders = [f.name for f in dir.iterdir() if f.is_dir()]
    return folders


def copy_folder(origin: Path, dest: Path, folders: list, excluded_folder : list): 
    print("Copying ")
    for folder in folders:
        origin_folder = origin / folder
        dest_folder = dest / folder 
        shutil.copytree(str(origin_folder), str(dest_folder),  
                        ignore=lambda src, names: [name for name in names if name in excluded_folder])
    


copy_folder(origin= raw_folder, dest=process_folder, folders=sel_folders, excluded_folder=excluded_steps)





