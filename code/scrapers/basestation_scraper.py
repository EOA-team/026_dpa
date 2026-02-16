from code.scrapers.selenium_utils import create_webdriver, BrowserType
from code.scrapers.base_scraper import BaseScraper
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from pathlib import Path
import time


class BasestationScraper(BaseScraper):
    def __init__(
        self,
        config_path: str | Path | None = None,
        driver_path: str | None = None,
        browser: BrowserType | None = None,
        timeout: int | None = None,
        output_path: str | None = None,
        service_url: str | None = None,
        username: str | None = None,
        password: str | None = None
    ):
        super().__init__(
            config_path=config_path,
            driver_path=driver_path,
            browser=browser,
            timeout=timeout,
            output_path=output_path,
            service_url=service_url,
            username=username,
            password=password
        )

    def login(self):
        testdelay_s = 0.2  # seconds
        time.sleep(testdelay_s)
        login_link = self.webdriver.find_element(by=By.ID, value= "ContentPlaceHolder1_m_LoginLink")
        login_link.click()
        time.sleep(testdelay_s)

        input_user = self.webdriver.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_UserName")
        input_pw = self.webdriver.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_Password")
        input_user.clear()
        input_user.send_keys(self.username)
        input_pw.clear()
        input_pw.send_keys(self.password)

        login_btn = self.webdriver.find_element(by=By.ID, value= "ContentPlaceHolder1_m_Login_LoginButton")
        login_btn.click()
        time.sleep(testdelay_s)
        
    def scrape(self) -> None:
        self.open()
        self.login()
        # Implementation TBD
        time.sleep(10)
        self.close()
        
    


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    scraper = BasestationScraper(browser="edge", 
                                 driver_path="C:/Tools/webdrivers/msedgedriver.exe",
                                 output_path="C:/Users/F80877978/Downloads/Rinex_output",
                                 service_url="https://shop.swipos.ch/",
                                 username=os.getenv("SWIPOS_USER"),
                                 password=os.getenv("SWIPOS_PW"),
                                 timeout=5)
    
   
        
    scraper.scrape()