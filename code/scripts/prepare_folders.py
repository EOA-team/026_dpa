from pathlib import Path
import shutil


# Set your Job
sel_flights = ["re112o_250514", "re112o_250519", "re112o_250610", "re112o_250619",
               "re112o_250717_1", "re112o_250717_2",
               "re112o_250723_1", "re112o_250723_2", "re112o_250723_3", "re112o_250723_4",
               "re112o_250807", "re112o_250813", "re112o_250903", "re112o_250918"]
raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")


def list_folders(path: Path) -> list:
    folders = [f.name for f in path.iterdir() if f.is_dir()]
    return folders


def filter_folders(folders: Path, filters: list[list[str]]) -> list[str]:
    """
    Filters subfolders of a given Path based on flexible keyword conditions.
    Returns a list of folder names as strings.

    Parameters:
        folders (Path): Path object pointing to a directory.
        filters (list[list[str]]): Each inner list represents a set of keywords 
                                   that must ALL be present in the folder name 
                                   (case-insensitive).

    Returns:
        list[str]: Filtered subfolder names as strings.
    """
    # Get all subfolders as Path objects
    folders_list = [f for f in folders.iterdir() if f.is_dir()]

    # Filter based on keyword rules (check folder name)
    filtered = [
        f.name for f in folders_list
        if any(all(keyword.lower() in f.name.lower() for keyword in rule) for rule in filters)
    ]
    return filtered


def copy_folders(origin: Path, dest: Path, folders: list[str], report: bool = False):
    """
    Copies selected folders from origin to destination.

    Parameters:
    - origin: Path to the source directory
    - dest: Path to the destination directory
    - folders: List of folder names to copy
    - report: If True, prints copy progress; otherwise, stays silent
    """
    origin = Path(origin)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)  # Ensure destination exists
    print(f"Copying {origin} -> {dest}")

    for folder_name in folders:
        src_path = origin / folder_name
        dst_path = dest / folder_name
        if src_path.exists() and src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            if report:
                print(f"Copied: {src_path.name} ✅")
        else:
            if report:
                print(f"Skipped (does not exist): {src_path.name} ❌")


def copy_flights(origin: Path, dest: Path, flights: list):
    for flight in flights:
        if not folder_exists(path=process_folder, folder=flight):
            filtered_folders = filter_folders(folders=raw_folder / flight,
                                              filters=[
                                                  # Include if it has "DSM"
                                                  ['dsm'],
                                                  # Include if it has both "RAD" and "VNIR"
                                                  ['rad', 'vnir'],
                                                  # Include if it has both "RAD" and "SWIR"
                                                  ['rad', 'swir']
                                              ])
            copy_folders(origin=origin / flight, dest=dest /
                         flight, folders=filtered_folders, report=True)


def rename_folders(process_folder: Path, flights: list, rename_lookup: list[dict], report: bool = False):
    """
    Renames subfolders in process_folder/flight according to rename_lookup.

    Parameters:
    - process_folder: Base processed folder path
    - flights: List of flight folder names
    - rename_lookup: List of dicts with 'filter' (list of keywords) and 'new_name'
    - report: If True, prints actions
    """
    for flight in flights:
        flight_folder = process_folder / flight
        if not flight_folder.exists():
            if report:
                print(f"Flight folder does not exist: {flight_folder}")
            continue

        for subfolder in flight_folder.iterdir():
            if subfolder.is_dir():
                folder_lower = subfolder.name.lower()
                new_name = subfolder.name  # default: keep original
                for entry in rename_lookup:
                    if all(keyword.lower() in folder_lower for keyword in entry["filter"]):
                        new_name = entry["new_name"]
                        break

                if new_name != subfolder.name:
                    new_path = subfolder.parent / new_name
                    subfolder.rename(new_path)
                    if report:
                        print(f"Renamed: {subfolder.name} -> {new_name}")
                elif report:
                    print(f"No change: {subfolder.name}")


def folder_exists(path: Path, folder: str) -> bool:
    existing_folders = list_folders(path)
    if folder in existing_folders:
        print(f"'{folder}' already exists!")
        return True
    return False


def main():
    copy_flights(origin=raw_folder, dest=process_folder, flights=sel_flights)
    rename_folders(
        process_folder,
        flights=sel_flights,
        rename_lookup=[
            {"filter": ["dsm"], "new_name": "DSM"},
            {"filter": ["rad", "vnir"], "new_name": "VNIR"},
            {"filter": ["rad", "swir"], "new_name": "SWIR"}
        ]
    )


if __name__ == "__main__":
    main()
