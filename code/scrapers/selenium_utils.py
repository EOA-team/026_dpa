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

Author: Pascal Ackermann
Branch: feature/4-rawdata_to_hd
"""

import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from typing import Literal, Union

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
    browser = browser.lower()
    
    try:
        logger.info(f"Initializing {browser.capitalize()} Driver...")
        
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.add_argument('--start-maximized')
            service = FirefoxService(executable_path=driver_path)
            driver = webdriver.Firefox(service=service, options=options)
            
        elif browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            service = ChromeService(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
        elif browser == "edge":
            options = webdriver.EdgeOptions()
            options.add_argument('--start-maximized')
            service = EdgeService(executable_path=driver_path)
            driver = webdriver.Edge(service=service, options=options)
            
        else:
            raise ValueError(f"Unsupported browser: {browser}. Choose from: 'firefox', 'chrome', 'edge'")
        
        logger.info(f"{browser.capitalize()} Driver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(
            f"Failed to initialize {browser.capitalize()} Driver: {e}\n"
            f"Check that the driver is installed at: {driver_path}"
        )
        raise

