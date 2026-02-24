"""This module provides an abstract base class `BaseScraper` and a configuration
dataclass `ScraperConfig` for web scrapers. 
"""
import os
from code.yamlconfig_helper import load_config_section, resolve_relative_paths
from code.scrapers.selenium_utils import create_webdriver, BrowserType
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast
from selenium.webdriver.support.ui import WebDriverWait  

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    def __init__(self, config_dict: dict | None = None, 
                 config_file_path: str | Path | None = None, 
                 config_file_section: str | None = None):
        """Load configuration from either a dictionary or a YAML file and initialize the scraper."""
        config = None
        if config_file_path is not None:
            config = self.load_config_from_file(config_file_path, config_file_section)
        elif config_dict is not None:
            config = self.load_config_from_dict(config_dict)
            
        if config is None:
             raise ValueError("Either config_dict or config_file_path must be provided")
        
        #Initialize scraper attributes from config
        #Service and login details
        self.service_url = str(config['service_url'])
        self.username = str(config['username'])
        self.password = str(config['password'])
        #Destination for downloaded data
        self.destination = Path(config['destination'])
        self.destination.mkdir(parents=True, exist_ok=True)

        # Initialize WebDriver
        self.webdriver = create_webdriver(
            driver_path=Path(config['driver_path']),
            browser=cast(BrowserType, config['browser'])
        )
        self.wait = WebDriverWait(self.webdriver, config['timeout'])


    
    def load_config_from_dict(self, config_dict: dict) -> dict:
        """Load configuration from dictionary."""
        base_path = config_dict['base_path']
        resolved_config = resolve_relative_paths(config=config_dict, base_path=base_path)
        return resolved_config
    
    def load_config_from_file(self, config_path: str | Path, section: str | None = None) -> dict:
        """Load configuration from YAML file."""
        config_dict = load_config_section(config_path, section) 
        base_path = Path(config_path).parent
        resolved_config = resolve_relative_paths(config=config_dict, base_path=base_path)
        return resolved_config
    
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
