"""This module provides an abstract base class `BaseScraper` and a configuration
dataclass `ScraperConfig` for web scrapers. 
"""
from code.scrapers.selenium_utils import create_webdriver, BrowserType
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast
from selenium.webdriver.support.ui import WebDriverWait
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


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, config: ScraperConfig | None = None, config_path: str | Path | None = None):
        # Load from config file or use provided config
        if config_path is not None:
            config_dict = self.load_config(config_path)
            config = ScraperConfig(
                driver_path=config_dict['driver_path'],
                browser=cast(BrowserType, config_dict['browser']),
                timeout=config_dict['timeout'],
                output_path=config_dict['output_path'],
                service_url=config_dict['service_url'],
                username=config_dict['username'],
                password=config_dict['password']
            )
        if config is None:
            raise ValueError("Either config or config_path must be provided")

        # Store configuration
        self.service_url = config.service_url
        self.username = config.username
        self.password = config.password

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
