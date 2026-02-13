from code.scrapers.basestation_scraper import BasestationScraper
from pyprojroot import here


if __name__ == "__main__": # Load environment variables from .env file
    config_path = here() / "code" / "tools" / "test_tool" / "config.yaml"
    scraper = BasestationScraper(config_path=config_path)
    scraper.scrape()