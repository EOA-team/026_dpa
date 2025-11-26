from pathlib import Path
import shutil


# Set your Job
sel_flights = ["re112o_250610", "re112o_250619","re112o_250717_2","re112o_250723_4",
               "re112o_250807", "re112o_250813", "re112o_250903", "re112o_250918"] # Relevant Flights for MT 
raw_folder = Path("D:/data/mjolnir")
process_folder = Path("E:/mjolnir_processing")

# This list defines filters for folders that should be copied.
# Each sublist contains strings that must all be present in the folder name to include it.
# Example 1: To start with raw data only, keep ['raw'] and comment out the rest.
# Example 2: To start with dsm, rad_vnir, and rad_swir already processed, comment out ['raw'] as it won't be needed.

folder_filter = [
    #['raw'],           # Include folders containing "raw"
    ['dsm'],           # Include folders containing "dsm"
    ['rad', 'vnir'],   # Include folders containing both "rad" and "vnir"
    ['rad', 'swir']    # Include folders containing both "rad" and "swir"
]


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
                                              filters= folder_filter)
            copy_folders(origin=origin / flight, dest=dest /
                         flight, folders=filtered_folders, report=True)


def rename_folders(base_folder: Path, flights: list, rename_lookup: list[dict], report: bool = False):
    """
    Renames subfolders in base_folder/flight according to rename_lookup.

    Parameters:
    - base_folder: Base  folder path
    - flights: List of flight folder names
    - rename_lookup: List of dicts with 'filter' (list of keywords) and 'new_name'
    - report: If True, prints actions
    """
    for flight in flights:
        flight_folder = base_folder / flight
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


def rename_files_to_base_full_extension(base_folder: Path, flights: list, target_subfolder: str, base_name: str = "DSM", report: bool = False):
    """
    Renames all files in a specific subfolder of each flight to a base name,
    keeping the full original extension (everything after the first dot), 
    or just the base name if there is no extension.

    Example:
    dem.tif.aux.xml -> DSM.tif.aux.xml
    demddddd       -> DSM

    Parameters:
    - base_folder: Path to the folder containing flight subfolders
    - flights: List of flight folder names
    - target_subfolder: Name of the subfolder inside each flight folder to process (e.g., "DSM")
    - base_name: The new base filename to use (default: "DSM")
    - report: If True, prints renaming actions
    """
    base_folder = Path(base_folder)

    for flight in flights:
        flight_folder = base_folder / flight / target_subfolder
        if not flight_folder.exists() or not flight_folder.is_dir():
            if report:
                print(f"Folder does not exist: {flight_folder}")
            continue

        for file_path in flight_folder.iterdir():
            if file_path.is_file():
                # Split the filename at the first dot
                parts = file_path.name.split(".", 1)
                if len(parts) == 1:
                    # No dot, just rename to base_name
                    new_name = base_name
                else:
                    # Keep everything after the first dot as extension
                    new_name = f"{base_name}.{parts[1]}"

                new_path = file_path.parent / new_name

                # Skip if the source and target are identical
                if new_path == file_path:
                    if report:
                        print(f"No change needed: {file_path.name}")
                    continue

                # Overwrite existing files if necessary
                if new_path.exists():
                    new_path.unlink()

                file_path.rename(new_path)
                if report:
                    print(f"Renamed: {file_path.name} -> {new_name}")


def folder_exists(path: Path, folder: str) -> bool:
    existing_folders = list_folders(path)
    if folder in existing_folders:
        print(f"'{folder}' already exists!")
        return True
    return False


def check_empty_subfolders(base_folder: Path, flights: list, target_subfolder: str, report: bool = True) -> list[str]:
    """
    Checks which flight folders have an empty target subfolder (e.g., DSM).

    Parameters:
    - base_folder: Path to the folder containing flight subfolders
    - flights: List of flight folder names
    - target_subfolder: Name of the subfolder to check inside each flight (default: "DSM")
    - report: If True, prints empty folders

    Returns:
    - List of flight folder names where the target subfolder is empty or does not exist
    """
    base_folder = Path(base_folder)
    empty_flights = []

    for flight in flights:
        flight_folder = base_folder / flight / target_subfolder
        if not flight_folder.exists() or not flight_folder.is_dir():
            if report:
                print(f"Folder does not exist: {flight_folder}")
            empty_flights.append(flight)
            continue

        # Check if folder is empty
        if not any(flight_folder.iterdir()):
            empty_flights.append(flight)
            if report:
                print(f"Empty folder: {flight_folder}")

    return empty_flights


def delete_flight_folders(base_folder: Path, flights_to_delete: list, report: bool = True):
    """
    Deletes entire flight folders inside the base folder.

    Parameters:
    - base_folder: Path to the folder containing flight subfolders
    - flights_to_delete: List of flight folder names to delete
    - report: If True, prints deletion actions
    """
    base_folder = Path(base_folder)

    for flight in flights_to_delete:
        flight_folder = base_folder / flight
        if flight_folder.exists() and flight_folder.is_dir():
            shutil.rmtree(flight_folder)
            if report:
                print(f"Deleted flight folder: {flight_folder}")
        else:
            if report:
                print(
                    f"Flight folder does not exist, skipping: {flight_folder}")


def main():
    copy_flights(origin=raw_folder, dest=process_folder, flights=sel_flights)
    rename_folders(
        base_folder=process_folder,
        flights=sel_flights,
        rename_lookup=[
            {"filter": ["dsm"], "new_name": "DSM"},
            {"filter": ["rad", "vnir"], "new_name": "VNIR"},
            {"filter": ["rad", "swir"], "new_name": "SWIR"}
        ],
        report=True
    )
    # Rename dem to DSM
    rename_files_to_base_full_extension(
        base_folder=process_folder,
        flights=sel_flights,
        target_subfolder="DSM",
        base_name="DSM",
        report=True
    )
    # Delete Unprocessed Flights 
    uncprocessed_flights = check_empty_subfolders(base_folder=process_folder, flights=list_folders(path=process_folder), target_subfolder="DSM")
    delete_flight_folders(base_folder=process_folder, flights_to_delete=uncprocessed_flights,report=True)


if __name__ == "__main__":
    main()
