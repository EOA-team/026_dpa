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
| Edge     | msedgedriver   | https://developer.microsoft.com/de-de/microsoft-edge/tools/webdriver |
+----------+----------------+----------------------------------------------------------+
"""

import logging
from typing import Literal, Union
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService


logger = logging.getLogger(__name__)

BrowserType = Literal["firefox", "chrome", "edge"]


def create_webdriver(
    browser: BrowserType,
    driver_path: str
) -> Union[webdriver.Firefox, webdriver.Chrome, webdriver.Edge]:
    """
    Create and configure a WebDriver instance for the specified browser.
    Example:
        >>> driver = create_webdriver('firefox', 'C:/tools/geckodriver.exe')
        >>> driver = create_webdriver('chrome', 'C:/tools/chromedriver.exe')
        >>> driver = create_webdriver('edge', 'C:/tools/msedgedriver.exe')
    """

    try:
        logger.info("Initializing %s Driver...", browser.capitalize())

        if browser == "firefox":
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument('--start-maximized')
            firefox_service = FirefoxService(executable_path=driver_path)
            firefox_driver = webdriver.Firefox(
                service=firefox_service, options=firefox_options)
            return firefox_driver

        if browser == "chrome":
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_service = ChromeService(executable_path=driver_path)
            chrome_driver = webdriver.Chrome(
                service=chrome_service, options=chrome_options)
            return chrome_driver

        if browser == "edge":
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--start-maximized')
            edge_service = EdgeService(executable_path=driver_path)
            edge_driver = webdriver.Edge(
                service=edge_service, options=edge_options)
            return edge_driver

        raise ValueError(
            f"Unsupported browser: {browser}. Choose from: 'firefox', 'chrome', 'edge'")

    except Exception as e:
        logger.error(
            "Failed to initialize %s Driver: %s\nCheck that the driver is installed at: %s",
            browser.capitalize(), e, driver_path
        )
        raise
