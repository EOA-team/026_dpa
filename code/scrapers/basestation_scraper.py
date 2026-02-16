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
from code.scrapers.base_scraper import BaseScraper, ScraperConfig
from dotenv import load_dotenv
from selenium.webdriver.common.by import By


class BasestationScraper(BaseScraper):
    """Scraper for Swiss Positioning Service (Swipos) to download RINEX observation data."""

    def __init__(self,
                 config: ScraperConfig | None = None,
                 config_path: str | Path | None = None,
                 ):
        super().__init__(
            config=config,
            config_path=config_path
        )

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

    def scrape(self) -> None:
        self.open()
        self.login()
        # Implementation TBD
        time.sleep(10)
        self.close()


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    manual_config = ScraperConfig(
        driver_path="C:/Tools/webdrivers/msedgedriver.exe",
        browser="edge",
        timeout=5,
        output_path="C:/Users/F80877978/Downloads/Rinex_output",
        service_url="https://shop.swipos.ch/",
        username=os.getenv("SWIPOS_USER"),
        password=os.getenv("SWIPOS_PW")
    )
    scraper = BasestationScraper(config=manual_config)

    scraper.scrape()
