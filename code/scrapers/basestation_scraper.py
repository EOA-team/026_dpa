"""
This scraper extracts high-precision GNSS reference station observations for differential 
post-processing of drone trajectory data.    

I accesses the Swiss Positioning Service (Swipos) and supports:
- Station selection: Choose from a network of reference stations across Switzerland.
- Time period filtering: Specify date ranges to retrieve relevant observation data.

All the data comes in RINEX format, which is a standard for GNSS data. 

"""


import time
from pathlib import Path
from datetime import datetime, timezone, tzinfo

from code.scrapers.base_scraper import BaseScraper

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait




class TrajectoryObservationTimeFetcher:
    """Fetches and holds observation period information from T04 trajectory files in APX folder."""

    def __init__(self, apx_folder: Path):
        self.apx_folder = apx_folder
        self._datetimes = self._load_datetimes()

        self.flight_start = self._datetimes[0]
        self.flight_end = self._datetimes[-1]
        self.duration_seconds = int(
            (self.flight_end - self.flight_start).total_seconds())

        self.date = self.flight_start.strftime("%d.%m.%Y")
        self.start_hour = self.flight_start.hour
        self.start_minute = self.flight_start.minute
        self.start_second = self.flight_start.second
        self.duration_hours = self.duration_seconds // 3600
        self.duration_minutes = (self.duration_seconds % 3600) // 60

    def _get_t04_filenames(self) -> list[str]:
        """Get all .t04 filenames in the APX folder."""
        return [f.name for f in self.apx_folder.glob("*.t04")]

    def _parse_datetime(self, filename: str, tzone: tzinfo = timezone.utc) -> datetime:
        """Extract datetime from T04 filename (expects YYYYMMDDHHMM before extension)."""
        name_part = filename.split('.')[0]
        dt = datetime.strptime(name_part[-12:], "%Y%m%d%H%M")
        return dt.replace(tzinfo=tzone)

    def _load_datetimes(self) -> list[datetime]:
        """Load and sort all datetimes from T04 files in the APX folder."""
        filenames = self._get_t04_filenames()
        if not filenames:
            raise ValueError(f"No .t04 files found in {self.apx_folder}")
        return sorted(self._parse_datetime(f) for f in filenames)


class BasestationScraper(BaseScraper):
    """Scraper for Swiss Positioning Service (Swipos) to download RINEX observation data."""

    def __init__(self, config: dict, observation_time: TrajectoryObservationTimeFetcher):
        super().__init__(config=config)
        self.observation_time = observation_time

    def login(self):
        """Log in to the Swipos service using credentials from the configuration."""
        testdelay_s = 0.2  # seconds
        time.sleep(testdelay_s)
        login_link = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_LoginLink")
        login_link.click()
        time.sleep(testdelay_s)

        input_user = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_UserName")
        input_pw = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_Password")
        input_user.clear()
        input_user.send_keys(self.username)
        input_pw.clear()
        input_pw.send_keys(self.password)

        login_btn = self.webdriver.find_element(
            by=By.ID, value="ContentPlaceHolder1_m_Login_LoginButton")
        login_btn.click()
        time.sleep(testdelay_s)

    def accept_cookies(self) -> None:
        """Accept cookies to gain access to the rest of the page."""
        cookies_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "accept")
            )
        )
        cookies_btn.click()

    def open_rinexshop(self):
        """ Navigate to the RINEX Shop page after logging in."""
        rinexshop_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "m_NavigationTreeViewt6")
            )
        )
        rinexshop_link.click()

    def open_neworder(self):
        """Open the 'New Order' page to start a new RINEX data request."""
        new_order_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_m_BtnNewOrder")
            )
        )
        new_order_link.click()

    def open_cors(self) -> None:
        """Open the Continuously Operating Reference Station (CORS) page."""
        cors_link = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_m_LinkCORS")
            )
        )
        cors_link.click()

    def select_reference_station(self, station_value: str = "ETH2") -> None:
        """Select a reference station from the dropdown."""
        select_element = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "m_RefStationListBox")
            )
        )
        # Wait until the specific option is present in the dropdown
        self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 f"#m_RefStationListBox option[value='{station_value}']")
            )
        )
        Select(select_element).select_by_value(station_value)

    def click_continue_to_time_selection(self) -> None:
        """Click the continue button to proceed to the time selection page."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContToTimeSelectionButton")
            )
        )
        btn.click()

    def _set_date(self, obs: TrajectoryObservationTimeFetcher) -> None:
        """Set the observation date in the SWIPOS form."""
        field = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "ctl00$ContentPlaceHolder1$mxDateTimeSelectionDate_input")
            )
        )
        field.clear()
        field.send_keys(obs.date)

    def _set_start_time(self, obs: TrajectoryObservationTimeFetcher) -> None:
        """Set the observation start time fields in the SWIPOS form."""
        fields = {
            "Hour":   obs.start_hour,
            "Minute": obs.start_minute,
            "Second": obs.start_second,
        }
        for unit, value in fields.items():
            field = self.wait.until(
                EC.visibility_of_element_located(
                    (By.ID, f"ContentPlaceHolder1_m_StartTime{unit}")
                )
            )
            field.clear()
            field.send_keys(str(value))

    def _set_duration(self, obs: TrajectoryObservationTimeFetcher) -> None:
        """Set the observation duration fields in the SWIPOS form."""
        fields = {
            "Hour":   obs.duration_hours,
            "Minute": obs.duration_minutes,
        }
        for unit, value in fields.items():
            field = self.wait.until(
                EC.visibility_of_element_located(
                    (By.ID, f"ContentPlaceHolder1_m_Duration{unit}")
                )
            )
            field.clear()
            field.send_keys(str(value))

    def _select_interval(self, interval_value: str) -> None:
        """Select the observation interval in seconds (default: 1s)."""
        select_element = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "ContentPlaceHolder1_m_IntervalDropDownList")
            )
        )
        Select(select_element).select_by_value(interval_value)

    def set_observation_period(self, obs: TrajectoryObservationTimeFetcher) -> None:
        """Set the observation start time and duration in the SWIPOS form."""
        self._set_date(obs)
        self._set_start_time(obs)
        self._set_duration(obs)
        self._select_interval("1")  # Set interval to 1 second
        time.sleep(5)  # Small delay to ensure form is ready

    def click_add_to_delivery(self) -> None:
        """Click the button to proceed to delivery options."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_NextToOrderButton")
            )
        )
        btn.click()

    def click_proceed_with_delivery_option(self) -> None:
        """Click the button to proceed to the delivery options page."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_m_BtnNext")
            )
        )
        btn.click()

    def select_output_format(self, format_value: str = "RINEX 3.03") -> None:
        """Select the output file format (default: RINEX 3.03)."""
        select_element = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "ContentPlaceHolder1_FileFormatDropDownList")
            )
        )
        Select(select_element).select_by_value(format_value)

    def click_generate_data(self) -> None:
        """Click the button to start generating the RINEX data."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_NextGenerateDataButton")
            )
        )
        btn.click()

    def click_proceed_with_delivery_details(self, timeout: int = 600) -> None:
        """Wait for data generation to complete and proceed to delivery details.

        Note: Data generation can take up to 10 minutes.
        """
        long_wait = WebDriverWait(self.webdriver, timeout)
        btn = long_wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_NextToOrderButton")
            )
        )
        btn.click()

    def select_delivery(self) -> None:
        """Select the first (topmost) delivery option from the radio buttons."""
        radio_buttons = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'input[type="radio"]')
            )
        )
        radio_buttons[0].click()

    def click_download(self) -> None:
        """Click the download button to download the RINEX data."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_m_BtnDownloadOrder")
            )
        )
        btn.click()

    def click_remove_item(self) -> None:
        """Click the remove item button after downloading the RINEX data."""
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "ContentPlaceHolder1_m_BtnRemoveItem")
            )
        )
        btn.click()

    def run(self) -> None:
        self.open()
        self.webdriver.maximize_window()
        self.accept_cookies()
        self.login()
        self.open_rinexshop()
        self.open_neworder()
        self.open_cors()
        self.select_reference_station(station_value="ETH2")
        self.click_continue_to_time_selection()
        self.set_observation_period(obs=self.observation_time)
        self.click_add_to_delivery()
        self.click_proceed_with_delivery_option()
        self.select_output_format(format_value="RINEX 3.03")
        self.click_generate_data()
        self.click_proceed_with_delivery_details()
        self.select_delivery()
        self.click_download()
        self.click_remove_item()

        # Implementation TBD
        self.close()
