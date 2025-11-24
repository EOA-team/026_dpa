from osgeo import gdal
from pathlib import Path

selected_Folder = Path("E:/251118_final_mt_ready/re112o_250918/output/georeferenced")

def get_tif_files(folder_path: Path) -> list[str]:
    folder = Path(folder_path)
    tif_files = [f.name for f in folder.glob("*.tif")]
    return tif_files

def change_file_extension(file_path: str , new_extension: str) -> str:
    file_path = Path(file_path)
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    return file_path.with_suffix(new_extension).name  


def main ():
    tif_files = get_tif_files(folder_path=selected_Folder)
    for filename in tif_files:
        dataset = gdal.Open(selected_Folder /filename)
        driver = gdal.GetDriverByName('ENVI')
        new_filename = change_file_extension(file_path=selected_Folder / filename, new_extension="bsq")
        driver.CreateCopy(selected_Folder/ new_filename, dataset)
        print(f"Conversion complete! ENVI file saved as: {new_filename}")
if __name__ == "__main__":
    main()
