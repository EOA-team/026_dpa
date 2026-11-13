from pathlib import Path

from osgeo import gdal

selected_folder = Path("E:/mjolnir_processing/re112o_250610/output/georeferenced")


def get_tif_files(folder_path: Path) -> list[str]:
    folder = Path(folder_path)
    tif_files = [f.name for f in folder.glob("*.tif")]
    return tif_files


def change_file_extension(file_path: str, new_extension: str) -> str:
    file_path = Path(file_path)
    if not new_extension.startswith("."):
        new_extension = "." + new_extension
    return file_path.with_suffix(new_extension).name


def main():
    tif_files = get_tif_files(folder_path=selected_folder)
    for filename in tif_files:
        dataset = gdal.Open(selected_folder / filename)
        driver = gdal.GetDriverByName("ENVI")
        new_filename = change_file_extension(
            file_path=selected_folder / filename, new_extension="bsq"
        )
        driver.CreateCopy(
            selected_folder / new_filename, dataset, options=["INTERLEAVE=BSQ"]
        )
        print(f"Conversion complete! ENVI file saved as: {new_filename}")


if __name__ == "__main__":
    main()
