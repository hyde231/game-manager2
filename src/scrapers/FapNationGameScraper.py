import re
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from typing import Dict, Iterator, Optional, Any, List
from html import unescape

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.Game import Game

class FapNationGameScraper(GameScraper):
    name: str = "FapNation"
    subdomain: Optional[str] = None
    domain: str = "fap-nation"
    suffix: str = "com"
    paths: Optional[List[str]] = None
    
    def __init__(self, game_instance: Game, **kwargs):
        self.cookiefile: str = "./data/cookies/fapnation_cookies.txt"
        self.headerfile: str = "./data/headers/fapnation_headers.json"
        self.base_url = "https://fap-nation.com"
        super().__init__(game_instance, cookiefile=self.cookiefile, headerfile=self.headerfile, **kwargs)
    
    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        (text, url) = self.get_text(url, method="cloudscraper")
        if not text:
            return {"url": url, "error": "Failed to fetch data"}
            
        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        soup = BeautifulSoup(text, "html.parser")
        data: Dict[str, Optional[str]] = {
            "url": url,
            "source": FapNationGameScraper.name
        }
        
        # Title
        headline = soup.find("h1")
        if headline:
            data["title"] = headline.text.split("[")[0].strip()

            if "[Final]" in headline.text or "[Final Version]" in headline.text:
                data["status"] = GameStatus.COMPLETED

        # Cover Image
        image = soup.find("meta", attrs={"property": "og:image"})
        if image:
            src = image.get("content")
            try:
                data_url = self.get_image(src, width=300, method="cloudscraper")
                data["cover_img"] = data_url
            except Exception as e:
                print(f"Image {src} failed to download. Error: ", e)

        # Last update
        last_update = soup.find("meta", attrs={"property": "og:updated_time"})
        if last_update:
            data["updated"] = parse_date(last_update.get("content")).date().isoformat()

        # Get Overview Tab
        overview_link = soup.find("a", attrs={"role":"tab"}, text="Overview")
        if overview_link:
            overview_id = overview_link.get("aria-controls")
            overview_div = soup.find("div", {"id":overview_id})
            if overview_div:
                data["description"] = overview_div.get_text(strip=True)

        # Get Info Tab
        info_link = soup.find("a", attrs={"role":"tab"}, text="Info")
        if info_link:
            info_id = info_link.get("aria-controls")
            info_div = soup.find("div", {"id":info_id})
            if info_div:
                # OS
                os_tag = info_div.find("b", string="OS")
                if os_tag and os_tag.next_sibling:
                    data["os"] = [os.strip().lower() for os in os_tag.next_sibling.replace(":"," ").split(",")]
                # Languages
                language_tag = info_div.find("b", string="Language")
                if language_tag and language_tag.next_sibling:
                    data["language"] = [lang.strip().lower() for lang in language_tag.next_sibling.replace(":"," ").split(",")]
                # Developer name
                developer_tag = info_div.find("b", string="Developer")
                if developer_tag and developer_tag.next_sibling:
                    data["developer"] = developer_tag.next_sibling.replace(":"," ").replace("–","").strip()

        # Get Changelog Tab
        changelog_link = soup.find("a", attrs={"role":"tab"}, text="Changelog")
        if changelog_link:
            changelog_id = changelog_link.get("aria-controls")
            changelog_div = soup.find("div", {"id":changelog_id})
            if changelog_div:
                version = changelog_div.find("strong")
                if version:
                    data["last_version"] = version.text.strip()

        # Tags
        data["tags"] = [ tag.get("content").lower().strip() for tag in soup.find_all("meta", attrs={"property": "article:tag"}) ]
        
        categories_div = soup.find("div", class_="tags")
        data["game_engine"] = GameEngine.UNKNOWN # Default
        if categories_div:
            # Extract Game Engine
            engine_mappings = {
                "Adrift": GameEngine.ADRIFT,
                "Flash": GameEngine.FLASH,
                "HTML": GameEngine.HTML,
                "JAVA": GameEngine.JAVA,
                "QSP": GameEngine.QSP,
                "RAGS": GameEngine.RAGS,
                "RenPy": GameEngine.RENPY,
                "Ren'Py": GameEngine.RENPY,
                "RPGM": GameEngine.RPGM,
                "TADS": GameEngine.TADS,
                "Unity": GameEngine.UNITY,
                "Unreal": GameEngine.UNREAL,
                "Unreal Engine": GameEngine.UNREAL,
                "WebGL": GameEngine.WEBGL,
                "Wolf RPG": GameEngine.WOLFRPG
            }
            for text, engine in engine_mapping.items():
                if headline.find("span", string=lambda t: t.lower() == text.lower() or t.lower() == f"[{text.lower()}]"):
                    data["game_engine"] = engine
                    break  # Exit the loop once a match is found

        return data
