"""
APX-20 Trajectory Data Scraper Module

A web scraper tool that uses Firefox with Selenium to fetch trajectory data
from the Applanix APX-20 GNSS-Inertial sensor connected to the Data Acquisition Unit
(DAU) onboard computer.

Connection Requirements
-----------------------
- APX-20 web interface accessible at: http://192.168.168.100/
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
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
import time

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_firefox_driver() -> webdriver.Firefox:
    """Create and configure Firefox WebDriver instance."""
    try:
        logger.info("Initializing Firefox WebDriver...")

        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--start-maximized')

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)

        logger.info("Firefox WebDriver initialized successfully")
        return driver

    except Exception as e:
        logger.error(f"Failed to initialize Firefox WebDriver: {e}")
        raise

def main():
    driver = create_firefox_driver()

    driver.get("http://192.168.168.100")
    time.sleep(5)

    driver.quit()


if __name__ == "__main__":
    main()
