"""
This scraper extracts high-precision GNSS reference station observations for differential 
post-processing of drone trajectory data.    

I accesses the Swiss Positioning Service (Swipos) and supports:
- Station selection: Choose from a network of reference stations across Switzerland.
- Time period filtering: Specify date ranges to retrieve relevant observation data.

All the data comes in RINEX format, which is a standard for GNSS data. 

"""

import os
import time
from pathlib import Path
from code.scrapers.base_scraper import BaseScraper
from code.yamlconfig_helper import replace_config_placeholder, resolve_relative_paths
from dotenv import load_dotenv
from selenium.webdriver.common.by import By


class BasestationScraper(BaseScraper):
    """Scraper for Swiss Positioning Service (Swipos) to download RINEX observation data."""

    def __init__(self, config: dict):
        super().__init__(config=config)

    def login(self):
        """Log in to the Swipos service using credentials from the configuration."""
        testdelay_s = 0.2  # seconds
        time.sleep(testdelay_s)
        login_link = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_LoginLink")
        login_link.click()
        time.sleep(testdelay_s)

        input_user = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_UserName")
        input_pw = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_Password")
        input_user.clear()
        input_user.send_keys(self.username)
        input_pw.clear()
        input_pw.send_keys(self.password)

        login_btn = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_LoginButton")
        login_btn.click()
        time.sleep(testdelay_s)

    def run(self) -> None:
        self.open()
        self.login()
        # Implementation TBD
        time.sleep(10)
        self.close()


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    CONFIG = {
        "browser": "edge",
        "driver_path": "./bin/msedgedriver.exe",
        "timeout": 5,
        "destination_path": "C:/Users/F80877978/Downloads/{flight_folder}/rinex/",
        "service_url": "https://shop.swipos.ch/",
        "username": BaseScraper.load_environment_variable("SWIPOS_USER"),
        "password": BaseScraper.load_environment_variable("SWIPOS_PW"),
    }
    FLIGHT_FOLDER = "re112o_250610"  # Example flight folder
    replaced_config = replace_config_placeholder(
        config=CONFIG,
        placeholder="{flight_folder}",
        replacement=FLIGHT_FOLDER
    )

    resolved_config = resolve_relative_paths(
        config=replaced_config,
        base_path=Path(os.getcwd())/"code"/"tools"/"postflightdtt"
    )

    scraper = BasestationScraper(config=resolved_config)

    scraper.run()
