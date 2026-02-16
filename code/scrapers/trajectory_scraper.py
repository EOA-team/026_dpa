""" Trajectory data scraper for APX-20 GNSS-Inertial sensor via web interface

Extracts data from external APX-20 sensor via web interface (http://192.168.168.100/).

Limitations
-----------
- Only accesses external APX-20 sensor (not internal APX-15), 
- Requires drone battery power and all cables plugged

Requirements
------------
See code/scrapers/selenium_utils.py for browser and WebDriver setup instructions

Note:
------------
 APX-15 internal sensor should be accessible directly via DAU, but could not yet manage to access it via
 the http://192.168.168.100/. Need to contact Applanix support. But for the moment APX-20 is sufficient.

"""

from pathlib import Path
import logging
import time
import os
from code.scrapers.base_scraper import BaseScraper, ScraperConfig
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class TrajectoryScraper(BaseScraper):
    """Trajectory Data Scraper for APX-20 GNSS-Inertial sensor"""
    def __init__(self,
                 config: ScraperConfig | None = None,
                 config_path: str | Path | None = None,
                 ):
        super().__init__(
            config=config,
            config_path=config_path
        )
    def login(self):
        
        """Login to APX-20 web interface."""
        # Wait for and switch to the iframe
        self.wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "main"))
        )
        # Switch to the nested dataFrame
        self.wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "dataFrame"))
        )

        # Type Username
        username_field = self.wait.until(
            EC.visibility_of_element_located((By.NAME, "username"))
        )
        username_field.clear()
        username_field.send_keys(self.username)

        # Type Password
        password_field = self.wait.until(
            EC.visibility_of_element_located((By.NAME, "password"))
        )
        password_field.clear()
        password_field.send_keys(self.password)

        # Submit the form instead of clicking the button
        form = self.webdriver.find_element(By.NAME, "theForm")
        form.submit()
        logger.info("Login Successful...")

    def scrape(self) -> None:
        self.open()
        self.login()
        time.sleep(10) # Time to press next page
        self.debug_page_state("after_login")
        time.sleep(10) # Time to press on data
        self.debug_page_state("after_go_to_data")
        time.sleep(10) # Time to press external data
        self.debug_page_state("after_external_data")
        time.sleep(10)
        self.close()

    def debug_page_state(self, step_name: str):
        """Debug helper to capture page state."""
        # Take screenshot
        screenshot_path = self.output_path / f"debug_{step_name}.png"
        self.webdriver.save_screenshot(str(screenshot_path))
        
        # Save page source
        html_path = self.output_path / f"debug_{step_name}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self.webdriver.page_source)
        
        print(f"Debug saved: {step_name}")

if __name__ == "__main__":

    load_dotenv()  # Load environment variables from .env file
    manual_config = ScraperConfig(
        driver_path="C:/Users/HySpex_user/tools/geckodriver.exe",
        browser="firefox",
        timeout=5,
        output_path="D:/HySpexAir/TrajectoryData/",
        service_url="http://192.168.168.100",
        username=os.getenv("APX_USER"),
        password=os.getenv("APX_PW")
    )
    scraper = TrajectoryScraper(config=manual_config)

    scraper.scrape()


