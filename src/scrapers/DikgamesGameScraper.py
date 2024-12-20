import re
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from typing import Dict, Iterator, Optional, Any, List

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.Game import Game

class DikgamesGameScraper(GameScraper):
    name: str = "Dikgames"
    subdomain: Optional[str] = None
    domain: str = "dikgames"
    suffix: str = "com"
    paths: Optional[List[str]] = None
    
    def __init__(self, game_instance: Game, **kwargs):
        super().__init__(game_instance, **kwargs)
        self.cookiefile = "" #"./data/cookies/fapnation_cookies.txt"
        self.base_url = "https://dikgames.com"

    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        (text, url) = self.get_text(url)
        soup = BeautifulSoup(text, "html.parser")

        data: Dict[str, Optional[str]] = {
            "url": url,
            "source": DikgamesGameScraper.name
        }

        #########################
        # TODO
        #########################

        return data
