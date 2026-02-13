from abc import ABC, abstractmethod
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from code.scrapers.selenium_utils import create_webdriver
import yaml

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(
        self, 
        config_path: str | Path | None = None,
        driver_path: str | None = None,
        browser: str | None = None,
        timeout: int | None = None,
        output_path: str | Path | None = None,
        service_url: str | None = None,
        username: str | None = None,
        password: str | None = None
    ):
        # If config_path provided, load from file
        if config_path is not None:
            config = self.load_config(config_path)
            driver_path = config['driver_path']
            browser = config['browser']
            timeout = config['timeout']
            output_path = config['output_path']
            service_url = config['service_url']
            username = config['username']
            password = config['password']
        else:
            # Validate that manual parameters are provided
            if not all([driver_path, browser, timeout, output_path]):
                raise ValueError(
                    "Either provide config_path OR all manual parameters "
                    "(driver_path, browser, timeout, output_path, service_url)"
                )
            
        # Store configuration
        self.service_url = service_url
        self.username = username
        self.password = password
        
        # Output path setup
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize WebDriver
        self.webdriver = create_webdriver(
            driver_path=driver_path,
            browser=browser
        )
        self.wait = WebDriverWait(self.webdriver, timeout)
    
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
