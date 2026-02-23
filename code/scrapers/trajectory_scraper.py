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
import os
import re
import time
import shutil
from code.scrapers.base_scraper import BaseScraper, ScraperConfig
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
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
        self._last_download_status: str = ""

    def switch_to_data_frame(self) -> None:
        """Switch WebDriver context into the nested dataFrame where page content is rendered.

        The APX-20 web interface uses a two-level frame structure:
          - 'main' iframe: top-level container loaded on page open
          - 'dataFrame' frame: nested inside 'main', holds all actual page content
            (file manager, login form, data logger, etc.)

        Any interaction with page elements must be preceded by this context switch,
        otherwise Selenium searches the top-level document and finds nothing.
        Always call switch_to.default_content() before calling this method
        to reset the context from a previous frame.
        """
        self.wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "main"))
        )
        self.wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "dataFrame"))
        )

    def login(self):
        
        """Login to APX-20 web interface."""
        self.switch_to_data_frame()

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
        # Wait 1 sec to make sure login works correctly
        time.sleep(1)
        logger.info("Login Successful...")


    def dismiss_splash_popup(self) -> None:
        """Dismiss the Applanix splash screen that appears on page open."""
        self.webdriver.switch_to.default_content()
        # Wait for the floating div to be visible
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "idFloatingDiv"))
        )
        # Dismiss via JS - same as clicking the red X
        self.webdriver.execute_script("hideFloatingDiv(true);")
        logger.info("Splash popup dismissed")


    def navigate_to_data_files(self) -> None:
        """Navigate to Data Logging > Data Files via the menu."""
        self.webdriver.switch_to.default_content()

        # Click "Data Logging" main menu item (index 2)
        data_logging_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@class='MenuMainItemDiv' and contains(text(), 'Data Logging')]")
            )
        )
        data_logging_link.click()

        # Click "Data Files" submenu item -> loads xml/fileManager.html into the iframe
        data_files_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@class='MenuSubItemDiv' and contains(., 'Data Files')]")
            )
        )
        data_files_link.click()
        logger.info("Navigated to Data Files")

    def select_internal_tab(self) -> None:
        """Navigate into the Internal directory in the file manager.

        The file manager shows Internal/External as directory links, not tabs.
        Clicking Internal calls changeDir('Internal') via JavaScript, which
        reloads the contents div with files from the /Internal path.
        """
        self.webdriver.switch_to.default_content()
        self.switch_to_data_frame()

        internal_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href=\"javascript:changeDir('Internal')\"]")
            )
        )
        internal_link.click()
        logger.info("Navigated into Internal directory")

    def select_all_files(self) -> None:
        """Click the Select All button in the file manager.

        Select All is rendered as an image link calling javascript:selectAll().
        Only appears after navigating into a subdirectory (not at root /).
        """
        # Wait for the selectAll link to appear after directory load
        select_all_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href='javascript:selectAll()']")
            )
        )
        select_all_link.click()
        logger.info("Selected all files")

    def download_selected_files(self) -> None:
        """Click the Download Selected Files button.

        Download is rendered as an image link calling javascript:downloadMultiple('').
        Triggers a confirmation dialog — handled via wait for alert.
        """
        download_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href=\"javascript:downloadMultiple('')\"]")
            )
        )
        download_link.click()
        logger.info("Download clicked, handling confirmation dialog...")

        # downloadMultiple() shows a confirm() dialog before downloading
        self.wait.until(EC.alert_is_present())
        alert = self.webdriver.switch_to.alert
        alert.accept()
        logger.info("Download confirmed")

    def wait_for_downloads_complete(self) -> None:
        """Wait until all files have been downloaded from the APX-20.
        During download the page updates contentsDiv with progress like:
            'Downloading[ 2 / 691 ]   filename.T04'
        and finally sets it to:
            'Downloads Complete'
        when all files are done. Poll this element until that final
        state is reached.
        """
        logger.info("Waiting for downloads to complete...")

        while True:
            text = self.webdriver.find_element(By.ID, "contentsDiv").text

            if text != self._last_download_status:
                logger.info("Download status: %s", text.strip())
                self._last_download_status = text

            if "Downloads Complete" in text:
                break

            time.sleep(1)

        logger.info("Downloads complete")

    def move_downloaded_files(self) -> None:
        """Move downloaded .T04 files from the browser downloads folder to output path.

        The browser saves files to the default downloads folder. This function
        collects all .T04 files from there and moves them to the configured
        output path.
        """
        downloads_folder = Path.home() / "Downloads"
        t04_files = list(downloads_folder.glob("*.T04"))

        if not t04_files:
            logger.warning("No .T04 files found in %s", downloads_folder)
            return

        logger.info("Found %d .T04 files to move", len(t04_files))

        for file in t04_files:
            destination = self.output_path / file.name
            shutil.move(str(file), str(destination))
            logger.info("Moved %s -> %s", file.name, destination)

        logger.info("All .T04 files moved to %s", self.output_path)

    def delete_selected_files(self) -> None:
        """Click the Delete Selected Files button.

        Delete is rendered as an image link calling javascript:deleteSelectedFiles().
        Triggers a confirmation dialog — handled via wait for alert.
        Only available when deleteAllowed is true on the device.
        """
        delete_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href='javascript:deleteSelectedFiles()']")
            )
        )
        delete_link.click()
        logger.info("Delete clicked, handling confirmation dialog...")

        self.wait.until(EC.alert_is_present())
        self.webdriver.switch_to.alert.accept()
        logger.info("Delete confirmed")

    def wait_for_delete_complete(self) -> None:
        """Wait until all files have been deleted from the APX-20.

        The page shows 'Delete Finished' when complete.
        """
        logger.info("Waiting for deletion to complete...")

        while True:
            text = self.webdriver.find_element(By.ID, "contentsDiv").text

            if text != self._last_download_status:
                logger.info("Delete status: %s", text.strip())
                self._last_download_status = text

            if "Delete Finished" in text:
                break

            time.sleep(1)

        logger.info("All files deleted")


    def scrape(self) -> None:
        self.open()
        self.dismiss_splash_popup()
        self.login()
        self.navigate_to_data_files()
        self.select_internal_tab()
        self.select_all_files()
        self.download_selected_files()
        self.wait_for_downloads_complete()

        if self.delete_after_download:
            self.select_all_files()
            self.delete_selected_files()
            self.wait_for_delete_complete()

        self.close()
        self.move_downloaded_files()


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
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    load_dotenv()  # Load environment variables from .env file
    manual_config = ScraperConfig(
        driver_path="C:/Users/HySpex_user/tools/geckodriver.exe",
        browser="firefox",
        timeout=5,
        output_path="D:/HySpexAir/TrajectoryData/",
        service_url="http://192.168.168.100",
        username=BaseScraper.load_environment_variable("APX_USER"),
        password=BaseScraper.load_environment_variable("APX_PW"),
        delete_after_download=True
    )
    scraper = TrajectoryScraper(config=manual_config)

    scraper.scrape()


