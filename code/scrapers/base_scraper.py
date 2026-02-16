from abc import ABC, abstractmethod
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from code.scrapers.selenium_utils import create_webdriver, BrowserType
import yaml

class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(
        self, 
        config_path: str | Path | None = None,
        driver_path: str |None = None,
        browser: BrowserType | None = None,
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
            if not all([driver_path, browser, timeout, output_path, service_url, username, password]):
                raise ValueError(
                    "When config_path is not provided, all parameters are required: "
                    "driver_path, browser, timeout, output_path, service_url, username, password"
                )
        
        # Type narrowing for mypy - we know these are not None after validation
        assert driver_path is not None
        assert browser is not None
        assert timeout is not None
        assert output_path is not None
        assert service_url is not None
        assert username is not None
        assert password is not None
        
        # Scraper URL and credentials
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
