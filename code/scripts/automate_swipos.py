from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from datetime import datetime, timezone, tzinfo
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import sys
import time
from pathlib import Path

rawdata_folder = Path(r"\\ags-vre-1040.agsad.admin.ch\Data-EODrone\drone\DERIS\raw")
flight_folder = rawdata_folder / r"RE\112o_pascal\re112o_250918_80m"
testdelay_s = 0.2
load_dotenv()

@dataclass
class SwiposObservationPeriod:
    date : str
    start_hour: int
    start_minute: int
    start_second: int
    duration_hours: int
    duration_minutes : int 

def get_t04_filenames(fpath: Path) -> list[str]:
    """
    Get all .t04 filenames in the 'apx' subfolder of the flight folder.

    Args:
        rawdata_folder (Path): The base path to the raw data folder.

    Returns:
        list[str]: A list of .t04 filenames (not full paths).
    """
    t04_files = list(fpath.glob("*.t04"))
    t04_filenames = [f.name for f in t04_files]

    return t04_filenames

def get_datetime_from_t04filename(
    
        t04filename: str, 
        tzone: tzinfo = timezone.utc 
        ) -> datetime:
    """
    Extracts date and time in UTC from a filename.
    Assumes the filename contains YYYYMMDDHHMM before the file extension.
    """
    # Remove file extension
    name_part = t04filename.split('.')[0]

    # Extract last 12 characters (YYYYMMDDHHMM)
    dt_str = name_part[-12:]

    # Parse to datetime
    dt = datetime.strptime(dt_str, "%Y%m%d%H%M")

    # Set timezone to UTC
    dt = dt.replace(tzinfo=tzone)

    return dt

def get_observation_period(apx_folder: Path) -> SwiposObservationPeriod:
    """
    Extracts observation information from the APX folder.

    """

    t04filenames = get_t04_filenames(fpath=apx_folder)
    t04datetimes = [get_datetime_from_t04filename(tmp_file) for tmp_file in t04filenames]

    
    flight_start = min(t04datetimes)
    flight_duration = max(t04datetimes) - min(t04datetimes)
    flight_duration_sec = int(flight_duration.total_seconds())
    return SwiposObservationPeriod(
        date =t04datetimes[0].strftime("%d.%m.%Y"),
        start_hour= flight_start.hour,
        start_minute=flight_start.minute,
        start_second=flight_start.second,
        duration_hours= flight_duration_sec // 3600,
        duration_minutes= (flight_duration_sec % 3600) //60 
    )




def main():
    obs_period = get_observation_period(apx_folder= flight_folder / "apx")


    myheaders = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"}
    webdrvr = webdriver.Firefox()
    webdrvr.maximize_window()     # Maximizes the window
    webdrvr.get("https://shop.swipos.ch/") #https://shop.swipos.ch/robots.txt --> Not existing

    time.sleep(testdelay_s)
    login_link = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_LoginLink")
    login_link.click()
    time.sleep(testdelay_s)

    input_user = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_UserName")
    input_pw = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_Password")
    input_user.clear()
    input_user.send_keys(os.getenv("SWIPOS_USER"))
    input_pw.clear()
    input_pw.send_keys(os.getenv("SWIPOS_PW"))

    login_btn = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_LoginButton")
    
    time.sleep(testdelay_s)
    
    login_btn.click()

    time.sleep(testdelay_s)

    rinexshop_link = webdrvr.find_element(by=By.ID, value= "m_NavigationTreeViewt6")
    rinexshop_link.click()
    time.sleep(testdelay_s)

    order_btn = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_BtnNewOrder")


    order_btn.click()
    time.sleep(testdelay_s)
    cors_link = webdrvr.find_element(by=By.ID, value= "ContentPlaceHolder1_m_LinkCORS")
    cors_link.click()
    time.sleep(testdelay_s)

    wait = WebDriverWait(webdrvr, 1)
    select_element = wait.until(EC.visibility_of_element_located((By.ID, "m_RefStationListBox")))
    dropdown_refstation = Select(select_element)
    dropdown_refstation.select_by_value("ETH2")
    time.sleep(testdelay_s)

    # Note! Need to click away cookies btn to have access to continue btn 
    cookiesaccept_btn = webdrvr.find_element(by=By.ID, value= "accept")
    cookiesaccept_btn.click()
    time.sleep(testdelay_s)

    continue_btn = webdrvr.find_element(by=By.ID, value=("ContToTimeSelectionButton"))
    continue_btn.click()
    time.sleep(testdelay_s)

    date_input = webdrvr.find_element(by=By.ID, value=("ctl00$ContentPlaceHolder1$mxDateTimeSelectionDate_input"))
    date_input.clear()
    date_input.send_keys(obs_period.date)
    time.sleep(testdelay_s)


    for time_unit in ["Hour", "Minute", "Second"]:
        starttime_input = webdrvr.find_element(by=By.ID, value=(f"ContentPlaceHolder1_m_StartTime{time_unit}"))
        starttime_input.clear()
        if time_unit == "Hour": 
            starttime_input.send_keys(obs_period.start_hour)
        elif time_unit == "Minute":
            starttime_input.send_keys(obs_period.start_minute)
        elif time_unit == "Second":
            starttime_input.send_keys(obs_period.start_second)

    time.sleep(testdelay_s)
    for time_unit in ["Hour", "Minute"]:
        duration_input = webdrvr.find_element(by=By.ID, value=(f"ContentPlaceHolder1_m_Duration{time_unit}"))
        duration_input.clear()
        if time_unit == "Hour": 
            duration_input.send_keys(obs_period.duration_hours)
        elif time_unit == "Minute":
            duration_input.send_keys(obs_period.duration_minutes)

    interval_sel = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_m_IntervalDropDownList"))
    dropdown_interval = Select(interval_sel)
    dropdown_interval.select_by_value("1")

    time.sleep(testdelay_s)

    toorder_btn = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_NextToOrderButton"))
    toorder_btn.click()
    time.sleep(testdelay_s)

    next_deliveryoption = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_m_BtnNext"))
    next_deliveryoption.click()
    time.sleep(testdelay_s)

    format_sel = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_FileFormatDropDownList"))
    dropdown_format = Select(format_sel)
    dropdown_format.select_by_value("RINEX 3.03")  

    time.sleep(testdelay_s)

    generate_btn = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_NextGenerateDataButton"))
    generate_btn.click()

    time.sleep(testdelay_s)
    wait = WebDriverWait(webdrvr, 600) #Wait max for 10min
    toorder_btn = wait.until(EC.visibility_of_element_located((By.ID, "ContentPlaceHolder1_NextToOrderButton")))
    toorder_btn.click()
    time.sleep(testdelay_s)

    radio_buttons = webdrvr.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
    radio_buttons[0].click() # only select upper most
    time.sleep(testdelay_s)

    

    download_btn = webdrvr.find_element(by=By.ID, value=("ContentPlaceHolder1_m_BtnDownloadOrder"))
    download_btn.click()
    time.sleep(30)


    webdrvr.close()









if __name__ == "__main__":
    main()

    

    
    

    
    

 



