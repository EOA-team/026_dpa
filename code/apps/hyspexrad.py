import time

from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers import (
    ApplicationManager, ControlFinder, ControlSimulator, UIAWrapper,DEFAULT_WAIT_TIME 
)


class HyspexRadApplication:
    class OutputFileFormat(StrEnum):
        INPUT = "input"
        BSQ = "bsq"
        BIP = "bip"
        BIL = "bil"
    
    class OutputDataType(StrEnum):
        INPUT = "input"
        UNSIGNED_INT_16BIT = "unsignedint"
        FLOAT_32BIT = "float"
    
    class InputImageType(StrEnum):
        RADIANCE = "radiometric"
        REFLECTANCE = "reflectance"

    class RGBFileFormat(StrEnum):
        BMP = "BMP"
        PNG = "PNG"
        JPG = "JPG"
    
    class SoftwareBinning:
        class Factor(StrEnum):
            X1 = "1X"
            X2 = "2X"
            X3 = "3X"
            X4 = "4X"
            X5 = "5X"
            X6 = "6X"

        class Sensor(StrEnum):
            SWIR = "swir"
            VNIR = "vnir"
    
        class Direction(StrEnum):
            ACROSS_TRACK = "across_track"
            SPECTRAL_DIRECTION = "spectral_direction"
            ALONG_TRACK = "along_track"


    
    def __init__(self, input_folders: list[Path], output_folders: list[Path]):
        self.input_folders= input_folders
        self.output_folders = output_folders
 

        # Application
        self.app_path : str = "G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/HyspexRad_V3.5.exe"
        self.work_dir : str = "G:/02. HySpex software/HyspexRadV3.5/HyspexRadV3.5/"
        self.window_title : str = "HyspexRad_V3.5"
        self.is_idl_application : bool = False
 
    def _set_output_fileformat(self, controlfinder: ControlFinder, fileformat: OutputFileFormat):
        radio_button = controlfinder.find_by_auto_id(control_type= "RadioButton",
                                                     auto_id=f"Widget.leftSideGroupBox.fileFormatGroupBox.{fileformat}formatradioButton")
        radio_button.select() 
    
    def _set_output_datatype(self, controlfinder: ControlFinder, datatype: OutputDataType):
        radio_button = controlfinder.find_by_auto_id(control_type= "RadioButton",
                                                     auto_id=f"Widget.leftSideGroupBox.dataTypeGroupBox.{datatype}typeradioButton")
        radio_button.select() 
    
    def _set_input_image_type(self, controlfinder: ControlFinder, image_type: InputImageType):
        checkbox = controlfinder.find_by_auto_id(control_type= "CheckBox",
                                                     auto_id=f"Widget.rightsideGroupBox.{image_type}CheckBox")
        if checkbox.get_toggle_state() != 1:  # 1 = checked
            checkbox.click()

    def _save_rgb_image(self, enable: bool, datatype :RGBFileFormat, controlfinder: ControlFinder):
        checkbox = controlfinder.find_by_auto_id(control_type="CheckBox",
                                                auto_id="Widget.rightsideGroupBox.groupBox.RgbImageCheckBox")
        checkbox_simulator = ControlSimulator(checkbox)
        if enable: 
            checkbox_simulator.enable_checkbox()
            combobox = controlfinder.find_by_auto_id(control_type="ComboBox",
                                                    auto_id="Widget.rightsideGroupBox.groupBox.RgbComboBox")
            combobox.select(datatype)
            
        else:
            checkbox_simulator.disable_checkbox()

    
    def _save_saturation_map(self, enable: bool, controlfinder: ControlFinder):
        checkbox = controlfinder.find_by_auto_id(control_type="CheckBox",
                                                        auto_id="Widget.rightsideGroupBox.groupBox.saturatedMapCheckBox")
        checkbox_simulator = ControlSimulator(checkbox)
        if enable:
            checkbox_simulator.enable_checkbox()
        else:
            checkbox_simulator.disable_checkbox()
    
    def _open_imageselection_window(self, controlfinder: ControlFinder):
        button  = controlfinder.find_by_auto_id(control_type="Button",
                                                  auto_id="Widget.rightsideGroupBox.openImageButton")
        button.invoke()
    
    def _get_imageselection_window(self, controlfinder: ControlFinder) -> UIAWrapper:
        self._open_imageselection_window(controlfinder)
        imageselection_window = controlfinder.find_child_window_by_title(window_title="Select Images")
        return imageselection_window
    
    def _select_input_images(self, controlfinder: ControlFinder, input_folder: Path):
        self._open_imageselection_window(controlfinder)
        img_sel_cf = ControlFinder(window=self._get_imageselection_window(controlfinder)) 

        #Write Path 
        filename_editbox = img_sel_cf.find_by_name(control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(input_folder))
        filename_editbox.type_keys("{ENTER}")

        # Mark all items
        itemslist= img_sel_cf.find_by_name(control_type="List", control_name="items view", exact=True)
        itemslist.type_keys("^a")  # Ctrl+A

        # Confirm Selection 
        open_btn = img_sel_cf.find_by_auto_id(control_type="Button", 
                                             auto_id="1")   
        open_btn.click()
        # Wait for window to close
        img_sel_cf.window.wait_not('exists', timeout=DEFAULT_WAIT_TIME)

        # Additional safety: ensure window is truly gone
        time.sleep(1)  # Small buffer to ensure cleanup


    def _get_softwarebinning_idx(self, sensor : SoftwareBinning.Sensor, direction: SoftwareBinning.Direction):
        BINNING_INDEX_MAP = {
            (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.ACROSS_TRACK): 0,
            (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.SPECTRAL_DIRECTION): 1,
            (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.ALONG_TRACK): 2,
            (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.ACROSS_TRACK): 3,
            (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.SPECTRAL_DIRECTION): 4,
            (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.ALONG_TRACK): 5,
        }
        return BINNING_INDEX_MAP[(sensor, direction)]
    
 
    def _set_softwarebinning(
        self, 
        controlfinder: ControlFinder, 
        binning_settings: dict[
            tuple[SoftwareBinning.Sensor, SoftwareBinning.Direction], 
            SoftwareBinning.Factor
        ]
    ):
        """Set software binning for multiple sensor/direction combinations.
    
        """
    
        sofwarebinning_comboboxes = controlfinder.find_all_by_name(
            control_type="ComboBox", 
            control_name="Software Binning"
        )
        
        # Apply each binning setting
        for (sensor, direction), binning_factor in binning_settings.items():
            idx = self._get_softwarebinning_idx(sensor, direction)
            sofwarebinning_comboboxes[idx].select(binning_factor)

    def set_output_folder(self, controlfinder: ControlFinder, folder_path: Path):
        editbox = controlfinder.find_by_auto_id(control_type="Edit", auto_id="Widget.leftSideGroupBox.folderEdit")
        editbox.set_edit_text(str(folder_path) + '\\')

    def start_processing(self, controlfinder: ControlFinder):
        button = controlfinder.find_by_auto_id(control_type="Button", auto_id="Widget.rightsideGroupBox.runButton")
        button.invoke()

    def wait_for_processing_to_complete(self, controlfinder: ControlFinder):
        """Wait until processing is complete by monitoring the progress bar.
        The progressbar should stay 100% for DEFAULT_WAIT_TIME seconds to consider processing complete.
        This is important because progressbar starts from 0% for each new image processed in a batch."""
        progress_bar = controlfinder.find_by_auto_id(control_type="ProgressBar", auto_id="Widget.leftSideGroupBox.progressBar")
        counter = 0
        while counter < DEFAULT_WAIT_TIME: 
            progress_value = progress_bar.iface_range_value.CurrentValue
            if progress_value >= 100:
                counter += 1
            elif progress_value < 100:
                counter = 0  # Reset counter if progress is less than 100%
            time.sleep(1)  # Check every second

    def run(self):
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                is_idl_application=self.is_idl_application) as hyspexrad_manager:
            main_window_cf = ControlFinder(window=hyspexrad_manager.window)
            main_window_cf.window.set_focus()

            # Settings
            self._set_output_fileformat(main_window_cf, self.OutputFileFormat.BSQ)
            self._set_output_datatype(main_window_cf, self.OutputDataType.FLOAT_32BIT)
            self._set_input_image_type(main_window_cf, self.InputImageType.RADIANCE)
            self._save_rgb_image(enable=True, datatype=self.RGBFileFormat.JPG, controlfinder=main_window_cf)
            self._save_saturation_map(enable=False, controlfinder=main_window_cf)

            # Software Binning Settings
            binning_settings = {
                (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.ACROSS_TRACK): 
                    self.SoftwareBinning.Factor.X1,
                (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.SPECTRAL_DIRECTION): 
                    self.SoftwareBinning.Factor.X1,
                (self.SoftwareBinning.Sensor.SWIR, self.SoftwareBinning.Direction.ALONG_TRACK): 
                    self.SoftwareBinning.Factor.X1,
                (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.ACROSS_TRACK): 
                    self.SoftwareBinning.Factor.X2,
                (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.SPECTRAL_DIRECTION): 
                    self.SoftwareBinning.Factor.X2,
                (self.SoftwareBinning.Sensor.VNIR, self.SoftwareBinning.Direction.ALONG_TRACK): 
                    self.SoftwareBinning.Factor.X2,
            }
            

            # Run Jobs
            for input_folder, output_folder in zip(self.input_folders, self.output_folders):
                self._select_input_images(controlfinder=main_window_cf, 
                                          input_folder=input_folder
                                          )
                # Make sure main window is focused after image selection 
                main_window_cf.window.set_focus() 
                # Software binning is set after selecting input images because when returning to main window it may destroys settings
                self._set_softwarebinning(controlfinder=main_window_cf, binning_settings=binning_settings) 
                output_folder.mkdir(parents=True, exist_ok=True)
                self.set_output_folder(controlfinder=main_window_cf, folder_path=output_folder)
                self.start_processing(controlfinder=main_window_cf)
                self.wait_for_processing_to_complete(controlfinder=main_window_cf)

              
