"""WebDriver utilities for browser automation.

This module provides helper functions to create and configure Selenium WebDriver
instances for different web browsers. WebDrivers act as translators between
Selenium commands and browser-specific APIs.

Browser-Specific Drivers
------------------------
Each browser requires its own driver executable:

+----------+----------------+----------------------------------------------------------+
| Browser  | Driver Name    | Download URL                                             |
+==========+================+==========================================================+
| Firefox  | geckodriver    | https://github.com/mozilla/geckodriver                   |
| Chrome   | chromedriver   | https://chromedriver.chromium.org                        |
| Edge     | msedgedriver   | https://developer.microsoft.com/microsoft-edge/webdriver |
| Safari   | safaridriver   | Built into macOS                                         |
+----------+----------------+----------------------------------------------------------+

Current Implementation
----------------------
Currently only Firefox WebDriver creation is implemented.

Author: Pascal Ackermann
Branch: feature/4-rawdata_to_hd
"""

import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

logger = logging.getLogger(__name__)


def create_firefox_driver(geckodriver_path : str) -> webdriver.Firefox:
    """Create and configure Firefox Driver instance and use Geckodriver as Translator"""
    try:
        logger.info("Initializing Firefox Driver...")

        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--start-maximized')

        service = Service(executable_path= geckodriver_path)
        driver = webdriver.Firefox(service=service, options=firefox_options)

        logger.info("Firefox Driver initialized successfully")
        return driver

    except Exception as e:
        logger.error(f"Failed to initialize Firefox Driver: {e}")
        raise