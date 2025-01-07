from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
from datetime import datetime, timedelta
from fake_useragent import UserAgent
import random
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ForexFactoryScraper:
    def __init__(self, proxy=None):
        self.driver = None
        self.proxy = proxy

    def _start_driver(self):
        """Start the Chrome driver with optional proxy settings."""
        us = UserAgent()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--user-agent={us.random}')

        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')

        # Additional options to make the bot less detectable
        options.add_argument('--disable-extensions')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-popup-blocking')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        logging.info("WebDriver started.")

    def _stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logging.info("WebDriver stopped.")

    def _wait_for_element(self, by, value, timeout=30):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logging.error(f"Timeout waiting for element: {value}")
            return None

    def _parse_row(self, row, current_date, year):
        """Parse a row of the calendar table."""
        date_element = row.find('td', {'class': 'calendar__date'})
        time_element = row.find('td', {'class': 'calendar__time'})
        currency_element = row.find('td', {'class': 'calendar__currency'})
        impact_element = row.find('td', {'class': 'calendar__impact'})
        event_element = row.find('td', {'class': 'calendar__event'})
        actual_element = row.find('td', {'class': 'calendar__actual'})
        forecast_element = row.find('td', {'class': 'calendar__forecast'})
        previous_element = row.find('td', {'class': 'calendar__previous'})

        # Update current_date if a new date is found
        if date_element and date_element.text.strip():
            current_date = date_element.text.strip()

        time_str = time_element.text.strip() if time_element else 'N/A'
        currency = currency_element.text.strip() if currency_element else 'N/A'
        impact = impact_element.find('span')['title'] if impact_element and impact_element.find('span') else 'N/A'
        event = event_element.text.strip() if event_element else 'N/A'
        actual = actual_element.text.strip() if actual_element else 'N/A'
        forecast = forecast_element.text.strip() if forecast_element else 'N/A'
        previous = previous_element.text.strip() if previous_element else 'N/A'

        return {
            'year': year,
            'date': current_date,
            'time': time_str,
            'currency': currency,
            'impact': impact,
            'event': event,
            'actual': actual,
            'forecast': forecast,
            'previous': previous
        }

    def scroll_and_load(self, scroll_increment=500, scroll_pause=1):
        """Scroll the page in increments until no new content is loaded."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 1  # Adjust based on the page structure

        while scroll_count < max_scrolls:
            scroll_count += 1
            # Scroll down in increments
            for i in range(0, last_height, scroll_increment):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(scroll_pause)  # Simulate human-like scrolling

            # Check if new content has loaded by comparing scroll heights
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # No new content loaded, exit the loop
            else:
                last_height = new_height  # Update last_height to the new height
                logging.debug(f"Scrolled to {new_height}px")


    def scrape_data(self, url):
        try:
            self._start_driver()
            self.driver.get(url)
            logging.info(f"Navigated to {url}")

            self.scroll_and_load()

            # Wait for the calendar table to be present
            calendar_table = self._wait_for_element(By.CLASS_NAME, 'calendar__table', timeout=60)
            if not calendar_table:
                logging.error("Failed to load the calendar table.")
                return pd.DataFrame()

            logging.info("Calendar table loaded successfully.")
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the calendarmini__header class
            header = soup.find('div', {'class': 'calendarmini__header'})
            if header:
                header_text = header.get_text(strip=True)
                logging.info(f"Found calendarmini__header: {header_text}")
                # Extract the year using regex to remove unwanted characters
                year_match = re.search(r'\b(\d{4})\b', header_text)
                if year_match:
                    year = int(year_match.group(1))
                    logging.info(f"Extracted year: {year}")
                else:
                    logging.error("Year not found in header_text.")
                    return pd.DataFrame()
            else:
                logging.warning("calendarmini__header class not found.")
                return pd.DataFrame()

            table = soup.find('table', {'class': 'calendar__table'})
            if not table:
                logging.error("Calendar table not found in page source.")
                return pd.DataFrame()

            rows = table.find_all('tr', {'class': 'calendar__row'})
            logging.info(f"Number of rows found: {len(rows)}")

            # Initialize current_date with the first date found
            current_date = None
            data = []
            for row in rows:
                parsed_row = self._parse_row(row, current_date, year)
                current_date = parsed_row['date']  # Update current_date for subsequent rows
                data.append(parsed_row)

            logging.info(f"Parsed {len(data)} rows of data.")
            return pd.DataFrame(data)

        except Exception as e:
            logging.error(f"An error occurred during scraping: {e}")
            return pd.DataFrame()
        finally:
            self._stop_driver()


    def scrape_historical_data(self, start_year, start_month, end_year, end_month):
        """
        Scrape historical data from the specified start date to the end date.
        
        :param start_year: int, the year to start scraping from
        :param start_month: int, the month to start scraping from (1-12)
        :param end_year: int, the year to end scraping at
        :param end_month: int, the month to end scraping at (1-12)
        :return: pd.DataFrame with all scraped data
        """
        all_data = pd.DataFrame()
        current_date = datetime.now()
        end_date = datetime(end_year, end_month, 1)
        month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        scrape_date = datetime(start_year, start_month, 1)

        while scrape_date <= min(end_date, current_date):
            month = month_names[scrape_date.month - 1]
            year = scrape_date.year

            try:
                url = f"https://www.forexfactory.com/calendar?month={month}.{year}"
                logging.info(f"Scraping data for {month.capitalize()} {year} from {url}")
                monthly_data = self.scrape_data(url)
                if not monthly_data.empty:
                    all_data = pd.concat([all_data, monthly_data], ignore_index=True)
                    logging.info(f"Scraped {len(monthly_data)} records for {month.capitalize()} {year}.")
                else:
                    logging.warning(f"No data scraped for {month.capitalize()} {year}.")

            except Exception as e:
                logging.error(f"An error occurred while scraping {month.capitalize()} {year}: {e}")

            # Move to the next month
            scrape_date = (scrape_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        return all_data
