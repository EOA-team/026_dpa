from code.scrapers.basestation_scraper import BasestationScraper
from pathlib import Path
import sys


def get_config_path() -> Path:
    """Get config path - works for both script and executable."""
    if getattr(sys, 'frozen', False):
        # Running as executable (PyInstaller)
        base_path = Path(sys.executable).parent
    else:
        # Running as script - use pyprojroot only in dev
        from pyprojroot import here
        base_path = here() / "code" / "tools" / "test_tool"
    
    return base_path / "config.yaml"


if __name__ == "__main__":
    print("Starting scraper...")
    print(f"Config path: {get_config_path()}")
    
    config_path = get_config_path()
    print(f"Config exists: {config_path.exists()}")
    
    scraper = BasestationScraper(config_path=config_path)
    scraper.scrape()