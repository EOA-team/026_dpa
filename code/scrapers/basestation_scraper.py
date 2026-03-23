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
from datetime import datetime, timezone, tzinfo

class TrajectoryObservationTimeFetcher:
    """Fetches and holds observation period information from T04 trajectory files in an APX folder."""

    def __init__(self, apx_folder: Path):
        self.apx_folder      = apx_folder
        self._datetimes      = self._load_datetimes()

        self.flight_start    = self._datetimes[0]
        self.flight_end      = self._datetimes[-1]
        self.duration_seconds = int((self.flight_end - self.flight_start).total_seconds())

        self.date             = self.flight_start.strftime("%d.%m.%Y")
        self.start_hour       = self.flight_start.hour
        self.start_minute     = self.flight_start.minute
        self.start_second     = self.flight_start.second
        self.duration_hours   = self.duration_seconds // 3600
        self.duration_minutes = (self.duration_seconds % 3600) // 60

    def _get_t04_filenames(self) -> list[str]:
        """Get all .t04 filenames in the APX folder."""
        return [f.name for f in self.apx_folder.glob("*.t04")]

    def _parse_datetime(self, filename: str, tzone: tzinfo = timezone.utc) -> datetime:
        """Extract datetime from T04 filename (expects YYYYMMDDHHMM before extension)."""
        name_part = filename.split('.')[0]
        dt = datetime.strptime(name_part[-12:], "%Y%m%d%H%M")
        return dt.replace(tzinfo=tzone)

    def _load_datetimes(self) -> list[datetime]:
        """Load and sort all datetimes from T04 files in the APX folder."""
        filenames = self._get_t04_filenames()
        if not filenames:
            raise ValueError(f"No .t04 files found in {self.apx_folder}")
        return sorted(self._parse_datetime(f) for f in filenames)

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
        time.sleep(60)
        self.close()


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file

    CONFIG = {
        "browser": "firefox",
        "driver_path": "C:/Tools/webdrivers/geckodriver.exe",
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
