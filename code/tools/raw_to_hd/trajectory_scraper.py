"""
APX-20 Trajectory Data Scraper Module

A web scraper tool that uses Firefox with Selenium to fetch trajectory data
from the Applanix APX-20 GNSS-Inertial sensor connected to the Data Acquisition Unit
(DAU) onboard computer.

Software Requirements
-----------------------
Geckodriver needs to be installed on DAU onboard computer.
It is installed here: "C:/Users/HySpex_user/tools/geckodriver.exe"
Installed Version : geckodriver-v0.36.0-win64.zip
https://github.com/mozilla/geckodriver/releases

Connection Requirements
-----------------------
- APX-20 web interface accessible at: http://192.168.168.100/
- User and Password are saved in .env file, the env variables are APX_USER and APX_PW
- DAU onboard computer must be connected to APX-20
- DAU must be connected to drone during operation

Functionality
-------------
- Automatically detects APX-20 availability via network reachability check
- Downloads all available T04 trajectory files from APX-20 web interface
- Saves downloaded files to D:/HySpexAir/TrajectoryData/
- Cleans up downloaded files from APX-20 to free storage space
- Provides detailed logging of all download operations

Author: Pascal Ackermann
Branch: feature/4-rawdata_to_hd
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from dotenv import load_dotenv
import os

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
import time

from  code.tools.raw_to_hd.selenium_utils import create_firefox_driver

import logging

logger = logging.getLogger(__name__)

# Configurations
GECKO_DRIVER_PATH = "C:/Users/HySpex_user/tools/geckodriver.exe" # Installation Path on DAU onboard computer




class TrajectoryScraper:
    """Trajectory Data Scraper"""
    def __init__(self, wait_time_seconds: int = 5):
        self.webdriver = create_firefox_driver(geckodriver_path=GECKO_DRIVER_PATH)
        self.wait  = WebDriverWait(self.webdriver, wait_time_seconds)
        self.service_url = "http://192.168.168.100" # Service to Fetch Trajectory Data from APX-20

    def open_page(self):
        self.webdriver.get(self.service_url)
        logger.info("Open Page")

    def close_page(self):
        self.webdriver.quit()
        logger.info("Close Page")




# def switch_to_iframe():
#     # Wait for the main iframe to load
#     wait = WebDriverWait(webdrvr, 10)
#     logger.info("Waiting for main iframe to load...")
#     main_frame = wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "main")))
#     logger.info("Switched to main iframe")
#
#
#     iframe = WebDriverWait(self.driver, self.wait_time).until(
#         EC.presence_of_element_located((By.TAG_NAME, "iframe"))
#     )
#     self.scroll_to_element(iframe)
#     self.driver.switch_to.frame(iframe)
#
#
# def login(webdrvr: webdriver.Firefox):
#     """Login to APX-20 web interface"""
#     load_dotenv()
#     wait = WebDriverWait(webdrvr, 10)
#     input_user = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
#     input_user.clear()
#     input_user.send_keys(os.getenv("APX_USER"))
#     input_pw = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
#     input_pw.clear()
#     input_pw.send_keys(os.getenv("APX_PW"))


def main():
    # Logger Settings
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scraper = TrajectoryScraper()
    scraper.open_page()
    time.sleep(5)
    scraper.close_page()



if __name__ == "__main__":
    main()
