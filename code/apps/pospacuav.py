"""Contains class to run PosPacUAV Application with Batch Manager"""

import re
from pathlib import Path
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, UIAWrapper, DEFAULT_WAIT_TIME, ControlNotFoundError
)
from code.file_utils import wait_for_file_creation
from string import Template


class PosPacUavApplication:
    """
    Class to simulate POSPac UAV which is only available as a Windows Application.
    Uses the Batch Manager to run batch files 
    Allows to load the settings, start the processing and wait until process is finished.
    ️Note: POSPac UAV must be installed on the system where this code is executed.
    """

    def __init__(self, input_folders: list[Path], output_folders: list[Path]):
        """Initialize PosPacUavApplication."""
        self.input_folders = input_folders
        self.output_folders = output_folders

        # Application
        self.app_path: str = "C:/Program Files/Applanix/POSPac UAV 9.3/POSPacUAV.exe"
        self.work_dir: str = "C:/Program Files/Applanix/POSPac UAV 9.3/"
        # Identify by auto_id insted of window_title because title changes dynamically
        self.window_auto_id: str = "MainFormBase"
        self.is_idl_application: bool = False

    def _click_batchmanager_button(self, controlfinder: ControlFinder) -> None:
        """Open the Batch Manager panel."""
        btn = controlfinder.find_by_auto_id(
            control_type="Button",
            auto_id="[Group : Batch Tools] Tool : BatchManager - Index : 0 ")
        btn.invoke()

    def _get_batchmanager_panel(self, controlfinder: ControlFinder) -> UIAWrapper:
        """Get the Batchmanager Panel window."""
        batchmanager_window = controlfinder.find_by_auto_id(
            control_type="Pane",
            auto_id="BatchManagerCmdUI"
        )
        return batchmanager_window

    def _open_batch_manager(self, controlfinder: ControlFinder) -> ControlFinder:
        """Open the Batch Manager panel if not already open and return its ControlFinder."""
        try:
            panel = self._get_batchmanager_panel(controlfinder)
            print("Batch Manager already open, skipping.")
            return ControlFinder(window=panel)
        except ControlNotFoundError:
            pass

        self._click_batchmanager_button(controlfinder)

        panel = self._get_batchmanager_panel(controlfinder)
        print("Batch Manager opened successfully.")
        return ControlFinder(window=panel)

    def _click_load_batch(self, controlfinder: ControlFinder) -> None:
        """Click the Load Batch button in the Batch Manager to open a batch file."""
        load_btn = controlfinder.find_by_name(
            control_type="Button",
            control_name="Load Batch")
        load_btn.click_input()

    def _enter_batchfile_path(self, controlfinder: ControlFinder, posbat_file: Path) -> None:
        """Enter the batch file path in the open file dialog and confirm."""
        filename_editbox = controlfinder.find_by_name(
            control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(posbat_file))
        filename_editbox.type_keys("{ENTER}")

    def _click_runbatch_button(self, controlfinder: ControlFinder) -> None:
        """Click the runbatch button to open the dropdown menu."""
        load_btn = controlfinder.find_by_name(
            control_type="Button",
            control_name="Run Batch")
        load_btn.click_input()

    def _reset_batchmanager(self, controlfinder: ControlFinder) -> None:
        """Clicking twice on run batch resets to initial state where no batch file is loaded"""
        self._click_batchmanager_button(controlfinder)
        self._click_batchmanager_button(controlfinder)

    def _run_all_projects(self, controlfinder: ControlFinder) -> None:
        """Select 'Run All Projects' in the Batch Manager."""
        self._click_runbatch_button(controlfinder)

        run_all = controlfinder.find_by_name(
            control_type="MenuItem",
            control_name="Run All Projects...")
        run_all.click_input()

    def _run_batch(self, main_cf: ControlFinder,
                   batch_cf: ControlFinder, posbat_file: Path) -> None:
        """"""
        self._click_load_batch(controlfinder=batch_cf)
        self._enter_batchfile_path(controlfinder=main_cf,
                                   posbat_file=posbat_file)
        self._run_all_projects(controlfinder=batch_cf)

    @staticmethod
    def parse_flight_window_from_extract_log(
            log_path: Path,
            margin_s: float,
            debug:    bool = False
    ) -> tuple[float, float]:
        """Parse Event 1 start/stop times from extract_Mission 1.log.
        Returns (start_time, stop_time) with margin added for IMU initialization.
        """
        pattern = re.compile(r"Event\s+1\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)")
        text = log_path.read_text()
        match = pattern.search(text)
        if not match:
            raise ValueError(f"No Event 1 found in {log_path}")

        start_time = float(match.group(1)) - margin_s
        stop_time = float(match.group(2)) + margin_s

        if debug:
            print(
                f"Flight window: {start_time:.3f}s - {stop_time:.3f}s (margin: ±{margin_s}s)")

        return start_time, stop_time

    @staticmethod
    def create_extract_only_batchfile(
            output_file:  Path,
            job_name:     str,
            input_folder: Path,) -> None:
        """Create a POSPac extract-only batch file from template for the given job.

        Args:
            output_file:  Path where the .posbat file will be saved.
            job_name:     Name of the job (e.g. 're112o_250610').
            input_folder: Path to the RAW data folder containing the apx subfolder.
        """
        apx_folder = input_folder / "apx"
        t04_files = sorted(apx_folder.glob("*.T04"))

        if not t04_files:
            raise ValueError(f"No .T04 files found in {apx_folder}")

        template_file = Path(__file__).parent / "templates" / \
            "extract_only_template.posbat"
        template = Template(template_file.read_text(encoding="utf-8"))

        xml_content = template.substitute(
            job_name=job_name,
            input_folder=str(input_folder),
            first_pos_file=t04_files[0].name,
            last_pos_file=t04_files[-1].name
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(xml_content, encoding="utf-8")
        print(f"Created batch file: {output_file}")

    @staticmethod
    def create_full_processing_batchfile(
            output_file:          Path,
            job_name:             str,
            input_folder:         Path,
            output_folder:        Path,
            start_time_total_sec: float,
            stop_time_total_sec:  float,
    ) -> None:
        """Create a POSPac full processing batch file from template.

        Args:
            output_file:          Path where the .posbat file will be saved.
            job_name:             Name of the job (e.g. 're112o_250610').
            input_folder:         Path to the RAW data folder.
            output_folder:        Path to the tmp/output folder.
            start_time_total_sec: GPS seconds for start of flight window.
            stop_time_total_sec:  GPS seconds for end of flight window.
        """
        apx_folder = input_folder / "apx"
        rinex_folder = input_folder / "rinex"
        rinex_station_id = "ETH2"

        t04_files = sorted(apx_folder.glob("*.T04"))
        if not t04_files:
            raise ValueError(f"No .T04 files found in {apx_folder}")

        rinex_extensions = {".25o", ".25n", ".25g", ".25l", ".25c"}
        rinex_files = sorted(
            f for f in rinex_folder.glob(f"{rinex_station_id}*")
            if f.suffix in rinex_extensions
        )
        if not rinex_files:
            raise ValueError(
                f"No RINEX files found for {rinex_station_id} in {rinex_folder}")

        pcap_files = list(input_folder.glob("*.pcap"))
        if not pcap_files:
            raise ValueError(f"No .pcap file found in {input_folder}")

        rinex_datafiles = "\n                    ".join(
            f"<DataFile>{f}</DataFile>" for f in rinex_files
        )

        template_file = Path(__file__).parent / "templates" / \
            "full_processing_template.posbat"
        template = Template(template_file.read_text(encoding="utf-8"))

        xml_content = template.substitute(
            job_name=job_name,
            input_folder=str(input_folder),
            output_folder=str(output_folder),
            first_pos_file=t04_files[0].name,
            last_pos_file=t04_files[-1].name,
            start_time_total_sec=start_time_total_sec,
            stop_time_total_sec=stop_time_total_sec,
            rinex_files=rinex_datafiles,
            pcap_file=pcap_files[0].name,
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(xml_content, encoding="utf-8")
        print(f"Created batch file: {output_file}")

    def run(self) -> None:
        """Run the POSPac UAV processing for each input/output folder pair (= job)."""

        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=None,  # Not needed when using auto_id
                                window_auto_id=self.window_auto_id,
                                is_idl_application=self.is_idl_application) as pospac_manager:

            main_window_cf = ControlFinder(window=pospac_manager.window)
            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                # Make sure Window is ready before starting next iteration
                main_window_cf.window.wait(
                    'enabled', timeout=DEFAULT_WAIT_TIME)
                main_window_cf.window.set_focus()
                # Next iteration
                job_name = input_folder.parent.name
                # Prepare Batch file "Extract only"
                tmp_posbat_file_path = output_folder / \
                    f"{job_name}_extract_only.posbat"
                self.create_extract_only_batchfile(output_file=tmp_posbat_file_path,
                                                   job_name=job_name,
                                                   input_folder=input_folder)
                # Run Batch file "Extract only"
                self._reset_batchmanager(controlfinder=main_window_cf)
                batchmanager_cf = self._open_batch_manager(main_window_cf)
                self._run_batch(main_cf=main_window_cf,
                                batch_cf=batchmanager_cf,
                                posbat_file=tmp_posbat_file_path)
                last_file_created_during_import = (tmp_posbat_file_path.parent
                                                   # e.g re112o_250610_extract_only
                                                   / tmp_posbat_file_path.stem
                                                   / "Mission 1" / "Extract"
                                                   / "gnss_nav_pri_interp_Mission 1.dat")
                wait_for_file_creation(
                    file_path=last_file_created_during_import,
                    timeout_s=900 # Expected: 10min --> Margin: 15min
                    )
                # Get Start and Stop Time for full processing batch file from extract log
                tmp_log_path = (tmp_posbat_file_path.parent
                                / tmp_posbat_file_path.stem  # e.g re112o_250610_extract_only
                                / "Mission 1" / "Extract"
                                / "extract_Mission 1.log")
                (start_time, stop_time) = self.parse_flight_window_from_extract_log(
                    margin_s=200.0,
                    log_path=tmp_log_path,
                    debug=True)

                # Prepare Batch file "Full processing"
                tmp_posbat_file_path = output_folder / \
                    f"{job_name}_full_processing.posbat"
                self.create_full_processing_batchfile(
                    output_file=tmp_posbat_file_path,
                    job_name=job_name,
                    input_folder=input_folder,
                    # output_foler :
                    # e.g. E:/mjolnir_processing/re112o_250610/tmp/re112o_250610_full_processing
                    output_folder=output_folder / tmp_posbat_file_path.stem,
                    start_time_total_sec=start_time,
                    stop_time_total_sec=stop_time
                )
                # Run Batch file "Full processing"
                self._reset_batchmanager(controlfinder=main_window_cf)
                batchmanager_cf = self._open_batch_manager(main_window_cf)
                self._run_batch(main_cf=main_window_cf,
                                batch_cf=batchmanager_cf,
                                posbat_file=tmp_posbat_file_path)

                last_file_created_during_processing = (tmp_posbat_file_path.parent
                                                       / tmp_posbat_file_path.stem
                                                       # e.g. re112o_250610_full_processing.log
                                                       / f"{tmp_posbat_file_path.stem}.log")
                wait_for_file_creation(file_path=last_file_created_during_processing,
                                       timeout_s=1200  # Expected: 11min --> Margin: 20min
                                       )


if __name__ == "__main__":
    test_output_folders = [Path("E:/mjolnir_processing/re112o_250610/tmp"),
                           Path("E:/mjolnir_processing/re112o_250918/tmp")]
    test_input_folders = [Path("E:/mjolnir_processing//re112o_250610/RAW"),
                          Path("E:/mjolnir_processing/re112o_250918/RAW")]
    pospacuav = PosPacUavApplication(input_folders=test_input_folders,
                                     output_folders=test_output_folders)

    pospacuav.run()
