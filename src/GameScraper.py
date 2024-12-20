from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import base64
import re
import time
import json
from dateutil.parser import parse as parse_date
import urllib.parse
from typing import Dict, List, Tuple, Iterator, Any, Optional, Callable

from src.Utility import dict_merge, slugify

import requests
import cloudscraper
from selenium import webdriver #pip install selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# Default options for the scraper
default_scraper_options = {}

class GameScraper(ABC):
    """
    Abstract base class for story scrapers.
    """

    # Class variables to determine scraper applicability
    name: str = ""
    subdomain: str = ""
    domain: str = ""
    suffix: str = ""
    paths: str = ""

    def __init__(self, game_instance : 'Game', cookiefile: Optional[str] = None, headerfile: Optional[str] = None, **kwargs):
        """
        Initialize the Scraper.

        Parameters:
            game_instance (Game): The game instance to be scraped.
            cookiefile (Optional[str]): Path to the Netscape cookie file.
            headerfile (Optional[str]): Path to the headers configuration file.
            **kwargs: Additional scraper options to override defaults.
        """
        self.cookiefile = cookiefile
        self.headerfile = headerfile
        self.cookies: Dict[str, str] = {}
        self.headers: Dict[str, str] = {}
        self.game_instance = game_instance
        self.scraper_options: Dict[str, Any] = dict_merge(default_scraper_options, **kwargs)

    def load_cookies(self) -> Dict[str, str]:
        """
        Load cookies from a Netscape cookie file using cookiejar.

        Returns:
            Dict[str, str]: Cookies as a dictionary.
        """
        if not self.cookiefile:
            return {}

        jar = requests.cookies.RequestsCookieJar()
        cookies = {}
        try:
            with open(self.cookiefile, "r") as file:
                for line in file:
                    if line.startswith("#") or not line.strip():
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 7:
                        domain, _, path, _, _, name, value = parts
                        jar.set(name, value, domain=domain, path=path)
                        cookies[name] = value
            self.cookies = cookies
        except Exception as e:
            print(f"Error loading cookies from {self.cookiefile}: {e}")
            self.cookies = {}
        #print("Loaded Cookies:", self.cookies)
        return self.cookies

    def load_headers(self) -> Dict[str, str]:
        """
        Load headers from a configuration file.

        Returns:
            Dict[str, str]: Headers as a dictionary.
        """
        if not self.headerfile:
            return {}

        try:
            with open(self.headerfile, "r", encoding="utf-8") as file:
                self.headers = json.load(file)
        except Exception as e:
            print(f"Error loading headers from {self.headerfile}: {e}")
            self.headers = {}
        #print("Loaded Headers:", self.headers)
        return self.headers

    def get_text(self, url: str, method: str = "request", arguments: List[str] = [], waitfunction: Optional[Callable] = None) -> (str, str):
        """
        Fetch the HTML content of the given URL.

        Parameters:
            url (str): The URL to fetch.
            method (str): One of "request", "cloudscraper", "chromedriver", or "undetectable chromedriver".
            arguments (List[str]): Arguments for the scraping method.
            waitfunction (Optional[Callable]): Function for custom waiting logic (e.g., clicks).

        Returns:
            str: The HTML content of the page.
            str: The final URL after any redirections.
        """
        # Ensure cookies and headers are loaded
        if not self.cookies:
            self.load_cookies()
        if not self.headers:
            self.load_headers()

        if method == "request":
            try:
                response = requests.get(url, cookies=self.cookies, headers=self.headers)
                response.raise_for_status()
                return response.text, url
            except Exception as e:
                print(f"Error fetching with requests: {e}")

        elif method == "cloudscraper":
            try:
                scraper = cloudscraper.create_scraper(browser='chrome', delay=10)
                response = scraper.get(url, cookies=self.cookies, headers=self.headers)
                response.raise_for_status()

                
                return response.text, response.url
            except Exception as e:
                print(f"Error fetching with cloudscraper: {e}")

        elif method in ["chromedriver", "undetectable chromedriver"]:
            try:
                options = uc.ChromeOptions() if method == "undetectable chromedriver" else Options()
                for arg in arguments:
                    options.add_argument(arg)
                driver = uc.Chrome(options=options) if method == "undetectable chromedriver" else webdriver.Chrome(options=options)
                driver.get(url)
                driver.implicitly_wait(10)
                if waitfunction:
                    waitfunction(driver)
                text = driver.page_source
                final_url = driver.current_url
                driver.quit()
                return text, final_url
            except Exception as e:
                print(f"Error fetching with {method}: {e}")

        return "", url

    def get_image(self, src: str, width: Optional[int] = None, method: str = "request", arguments: List[str] = []) -> Optional[str]:
        """
        Fetch an image from the given src, optionally resize it, and return it as a Data URL.

        Parameters:
            src (str): The image's src attribute.
            width (Optional[int]): Standard width to resize the image. If None, no resizing is performed.
            method (str): Method to use for fetching the image: "request", "cloudscraper", "chromedriver", or "undetectable chromedriver".
            arguments (List[str]): Arguments for the chromedriver options if used.

        Returns:
            Optional[str]: The Data URL of the image, or None if an error occurs.
        """
        # Ensure cookies and headers are loaded
        if not self.cookies:
            self.load_cookies()
        if not self.headers:
            self.load_headers()
        
        try:
            # Fetch the image using the specified method
            if method == "request":
                response = requests.get(src, cookies=self.cookies, headers=self.headers)
                response.raise_for_status()
                content = response.content
            elif method == "cloudscraper":
                scraper = cloudscraper.create_scraper()
                response = scraper.get(src, cookies=self.cookies, headers=self.headers)
                response.raise_for_status()
                content = response.content
            elif method in ["chromedriver", "undetectable chromedriver"]:
                options = uc.ChromeOptions() if method == "undetectable chromedriver" else Options()
                for arg in arguments:
                    options.add_argument(arg)
                driver = uc.Chrome(options=options) if method == "undetectable chromedriver" else webdriver.Chrome(options=options)
                driver.get(src)
                image_element = driver.find_element(By.TAG_NAME, "img")
                image_src = image_element.get_attribute("src")
                driver.quit()

                response = requests.get(image_src, cookies=self.cookies, headers=self.headers)
                response.raise_for_status()
                content = response.content
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Open the image with Pillow
            img = Image.open(BytesIO(content))

            # Resize the image if width is specified
            if width:
                aspect_ratio = img.height / img.width
                new_height = int(width * aspect_ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            # Convert the image to a Data URL
            buffer = BytesIO()
            img_format = img.format or "PNG"
            img.save(buffer, format=img_format)
            data_url = f"data:image/{img_format.lower()};base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            return data_url

        except Exception as e:
            print(f"Error fetching or processing image: {e}")
            return None

    @abstractmethod
    def get_data(self, **kwargs) -> Dict[str, Any]:
        """
        Abstract method to extract data from HTML or raw text.

        Must be implemented by subclasses.

        Parameters:
            **kwargs: Additional arguments.

        Returns:
            Dict[str, Any]: Extracted data.
        """
        pass

    def get_main_thread(self, **kwargs) -> Dict[str, Any]:
        """
        Abstract method to extract data from HTML or raw text.

        Must be implemented by subclasses.

        Parameters:
            **kwargs: Additional arguments.

        Returns:
            Dict[str, Any]: Extracted data.
        """
        pass
