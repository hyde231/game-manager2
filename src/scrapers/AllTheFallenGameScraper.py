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
        text, final_url = self.get_text(url, method="cloudscraper")
        if not text:
            return {"url": url, "error": "Failed to fetch data"}

        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        soup = BeautifulSoup(text, "html.parser")

        data: Dict[str, Optional[str]] = {
            "url": url,
            "source": AllTheFallenGameScraper.name
        }

        #########################
        # TODO
        #########################


        version_dl = soup.find("dl", {"data-field": "version_number"})
        if version_dl:
            data["last_version"] = version_dl.find("dd").text

        published = soup.find("time")
        if published:
            data["published"] = parse_date(published.text)
        last_update = soup.find("dl", {"data-field": "last_update"})
        if last_update:
            data["updated"] = parse_date(last_update.find("dd").text)

        taglist = soup.find("dl", class_="tagList")
        if taglist:
            data["tags"] = list(set([ tag.text.strip() for tag in taglist.find_all("a", class_= "tagItem") ]))

        headline = soup.find("title")
        headline_text = str(headline)
        if 'Complete -' in headline_text:
            data["status"] = "completed"
        elif '>Abandoned -' in headline_text:
            data["status"] = "abandoned"
        elif '>Hiatus -' in headline_text:
            data["status"] = "abandoned" # treat it as abandoned???
        return data

        