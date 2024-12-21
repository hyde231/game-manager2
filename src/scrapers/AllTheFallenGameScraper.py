import re
from bs4 import BeautifulSoup
from typing import Dict, Iterator, Optional, Any, List
from dateutil.parser import parse as parse_date
from html import unescape

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.Game import Game

class AllTheFallenGameScraper(GameScraper):
    name: str = "AllTheFallen"
    subdomain: Optional[str] = None
    domain: str = "allthefallen"
    suffix: str = "moe"
    paths: Optional[List[str]] = None
    
    def __init__(self, game_instance: Game, **kwargs):
        super().__init__(game_instance, **kwargs)
        self.cookiefile = "./data/cookies/allthefallen_cookies.txt"
        self.base_url = "https://allthefallen.moe"

    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        arguments = [
            "--headless=new", # for Chrome >= 109
            "--disable-gpu",
            "--no-sandbox",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled"
        ]
        def waitfunction(driver,title):
            WebDriverWait(driver, 15).until(
                lambda driver: driver.title != title
            )
        text, final_url = self.get_text(url, method="undetectable chromedriver", arguments=arguments, waitfunction=waitfunction)
        
        if not text:
            return {"url": url, "error": "Failed to fetch data"}

        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        soup = BeautifulSoup(text, "html.parser")

        data: Dict[str, Optional[str]] = {
            "url": url,
            "source": AllTheFallenGameScraper.name
        }

        



        return data

        