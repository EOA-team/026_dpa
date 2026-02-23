"""This module provides an abstract base class `BaseScraper` and a configuration
dataclass `ScraperConfig` for web scrapers. 
"""
from code.scrapers.selenium_utils import create_webdriver, BrowserType
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast
from selenium.webdriver.support.ui import WebDriverWait
import os
import yaml


@dataclass
class ScraperConfig:
    """Configuration for web scrapers."""
    driver_path: str
    browser: BrowserType
    timeout: int
    output_path: str | Path
    service_url: str
    username: str
    password: str
    delete_after_download: bool


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, config: ScraperConfig | None = None, config_path: str | Path | None = None):
        # Load from config file or use provided config
        if config_path is not None:
            config_dict = self.load_config(config_path)
            scraper_dict = config_dict['scraper']
            config = ScraperConfig(
                driver_path=scraper_dict['driver_path'],
                browser=cast(BrowserType, scraper_dict['browser']),
                timeout=scraper_dict['timeout'],
                output_path=scraper_dict['output_path'],
                service_url=scraper_dict['service_url'],
                username=scraper_dict['username'],
                password=scraper_dict['password'],
                delete_after_download=scraper_dict['delete_after_download']
            )
        if config is None:
            raise ValueError("Either config or config_path must be provided")

        # Service configuration
        self.service_url = config.service_url
        self.username = config.username
        self.password = config.password
        self.delete_after_download = config.delete_after_download

        # Output path setup
        self.output_path = Path(config.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize WebDriver
        self.webdriver = create_webdriver(
            driver_path=config.driver_path,
            browser=config.browser
        )
        self.wait = WebDriverWait(self.webdriver, config.timeout)

    @staticmethod
    def load_config(config_path: str | Path) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def load_environment_variable(variable_name : str) -> str:
        """Load environment variable."""
        value = os.getenv(variable_name)
        if value is None:
            raise ValueError(f"{variable_name} must be set in environment / .env file")
        return value

    @abstractmethod
    def scrape(self) -> None:
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
