import time

from pathlib import Path
from enum import StrEnum
from code.pywinauto_helpers_new import (
    ApplicationManager, DesktopManager, ControlFinder, ControlSimulator, UIAWrapper 
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



    def __init__(self):
        self.jobs: list[str] = ["re112o_250610", "re112o_250918"]
        
        # Base folders
        self.input_basefolder = Path("D:/data/mjolnir")
        self.output_basefolder = Path("E:/mjolnir_processing")

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
    
    def _get_next_job_folder(self):
        if not self.jobs:
            raise ValueError("No more jobs available.")
        job_name = self.jobs.pop(0)
        job_folder = self.output_basefolder / job_name
        return job_folder
    
    def _select_input_images(self, controlfinder: ControlFinder, input_folder: Path):
        self._open_imageselection_window(controlfinder)
        img_sel_cf = ControlFinder(window=self._get_imageselection_window(controlfinder)) 

        #Write Path 
        filename_editbox = img_sel_cf.find_by_name(control_type="Edit", control_name="file name:", exact=True)
        filename_editbox.set_edit_text(str(self._get_next_job_folder() / "RAW"))
        filename_editbox.type_keys("{ENTER}")

        # Mark all items
        itemslist= img_sel_cf.find_by_name(control_type="List", control_name="items view", exact=True)
        itemslist.type_keys("^a")  # Ctrl+A

        # Confirm Selection 
        open_btn = img_sel_cf.find_by_auto_id(control_type="Button", 
                                             auto_id="1")   
        open_btn.click()
    
    
    def _set_softwarebinning(self, controlfinder: ControlFinder ):
        controlfinder.window.set_focus()
        swir_across_track = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=0)
        swir_across_track.select("1X")

        swir_spectral_direction = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=1)
        swir_spectral_direction.select("1X")

        swir_along_track = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=2)
        swir_along_track.select("1X")

        vnir_across_track = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=3)
        vnir_across_track.select("2X")

        vnir_spectral_direction = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=4)
        vnir_spectral_direction.select("2X")

        vnir_along_track = controlfinder.find_by_name(control_type="ComboBox", control_name="Software Binning", found_index=5)
        vnir_along_track.select("2X")
            



    def run (self):
        with ApplicationManager(app_path=self.app_path,
                                work_dir=self.work_dir,
                                window_title=self.window_title,
                                is_idl_application=self.is_idl_application) as hyspexrad_manager:
            main_window_cf = ControlFinder(window=hyspexrad_manager.window)

            # Settings
            self._set_output_fileformat(main_window_cf, self.OutputFileFormat.BSQ)
            self._set_output_datatype(main_window_cf, self.OutputDataType.FLOAT_32BIT)
            self._set_input_image_type(main_window_cf, self.InputImageType.RADIANCE)
            self._save_rgb_image(enable=False, datatype=self.RGBFileFormat.JPG, controlfinder=main_window_cf)
            self._save_saturation_map(enable=False, controlfinder=main_window_cf)


            for job in range(len(self.jobs)):
                self._select_input_images(main_window_cf, input_folder=self.input_basefolder)
                self._set_softwarebinning(main_window_cf)
                time.sleep(3)  # Placeholder for actual processing time
            


            


  
           
            


        
            
            

    
        



if __name__ == "__main__":

    hyspexrad_app = HyspexRadApplication()
    hyspexrad_app.run()
    
    

