"""This module provides an abstract base class `BaseScraper` and a configuration
dataclass `ScraperConfig` for web scrapers. 
"""
import os
from code.scrapers.selenium_utils import create_webdriver, BrowserType
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast
from selenium.webdriver.support.ui import WebDriverWait  

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    def __init__(self, config: dict ):
        self.service_url = str(config['service_url'])
        self.username = str(config['username'])
        self.password = str(config['password'])

        #Destination for downloaded data
        self.destination_path = Path(config['destination_path'])
        self.destination_path.mkdir(parents=True, exist_ok=True)
        # Initialize WebDriver
        self.webdriver = create_webdriver(
            driver_path=Path(config['driver_path']),
            browser=cast(BrowserType, config['browser'])
        )
        self.wait = WebDriverWait(self.webdriver, config['timeout'])
    
    @staticmethod
    def load_environment_variable(variable_name : str) -> str:
        """Load environment variable."""
        value = os.getenv(variable_name)
        if value is None:
            raise ValueError(f"{variable_name} must be set in environment / .env file")
        return value

    @abstractmethod
    def run(self) -> None:
        """Abstract method - implement scraping logic in subclasses."""
        pass

    def close(self) -> None:
        """Close WebDriver connection."""
        if self.webdriver:
            self.webdriver.quit()

    def open(self) -> None:
        """Open the target web page."""
        if self.service_url:
            self.webdriver.get(self.service_url)
