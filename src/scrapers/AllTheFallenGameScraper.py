import re
from bs4 import BeautifulSoup
from typing import Dict, Iterator, Optional, Any, List
from dateutil.parser import parse as parse_date
from html import unescape

from selenium.webdriver.support.ui import WebDriverWait

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.Game import Game

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

        # Title
        title_tag = soup.find("h1", class_="p-title-value")
        if title_tag:
            pure_text_nodes = [child for child in title_tag.children if child.name is None]
            title = ''.join(pure_text_nodes).strip()
            title = title.split("[")[0].strip()
            data["title"] = title

        # Cover image
        article = soup.find("article", class_="message-body")
        if article:
            cover = article.find("img")
            if cover:
                src = cover.get("src")
                try:
                    data_url = self.get_image(src, width=300, method="undetectable chromedriver", arguments=arguments, waitfunction=waitfunction)
                    data["cover_img"] = data_url
                except Exception as e:
                    print(f"Image {src} failed to download. Error: ", e)
        
        # Description
        description_tag = soup.find("meta", property="og:description")
        if description_tag:
            data["description"] = description_tag.get("content")


        # Version
        version_dl = soup.find("dl", {"data-field": "version_number"})
        if version_dl:
            data["last_version"] = version_dl.find("dd").text.strip()

        # Published
        published = soup.find("time")
        if published:
            data["published"] = parse_date(published.text).date().isoformat()

        # Last update
        last_update = soup.find("dl", {"data-field": "last_update"})
        if last_update:
            try:
                data["updated"] = parse_date(last_update.find("dd").text.strip()).date().isoformat()
            except Exception as e:
                print(f"Last update failed. Error: ", e)

        # Developer
        developer_tag = soup.find("dl", {"data-field": "developer_name"})
        if developer_tag:
            data["developer"] = developer_tag.find("dd").text.lower().strip().replace("\n",",")

        # OS
        os_tag = soup.find("dl", {"data-field": "os_support"})
        if os_tag:
            data["os"] = [os.text.strip() for os in os_tag.find_all("li")]

        # Language
        language_tag = soup.find("dl", {"data-field": "language"})
        if language_tag:
            data["language"] = [l.strip() for l in language_tag.find("dd").text.split(",")]

        # Tags
        taglist = soup.find("dl", class_="tagList")
        if taglist:
            data["tags"] = list(set([ tag.text.lower().strip() for tag in taglist.find_all("a", class_= "tagItem") ]))

        headline = soup.find("title")
        if headline:
            headline_text = headline.text

        # Extract Status
        if "Active -" in headline_text:
            data["status"] = GameStatus.ACTIVE
        if "Complete -" in headline_text:  #not "elif" because it could overrule status Active
            data["status"] = GameStatus.COMPLETED
        elif "Abandoned -" in headline_text:
            data["status"] = GameStatus.ABANDONED
        elif "Onhold -" in headline_text or "Hiatus - " in headline_text:
            data["status"] = GameStatus.ONHOLD
        else:
            data["status"] = GameStatus.UNKNOWN

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
        data["game_engine"] = GameEngine.UNKNOWN # Default
        for text, engine in engine_mappings.items():
            if text+" -" in headline_text:
                data["game_engine"] = engine
                break  # Exit the loop once a match is found

        # Extract Render Engine
        render_mappings = {
            "AI": GameRender.AI,
            "DAZ": GameRender.DAZ,
            "Hand Drawn": GameRender.HAND_DRAWN,
            "HS": GameRender.HS,
            "HS2": GameRender.HS2,
            "Koikatsu": GameRender.KOIKATSU,
            "TK17": GameRender.TK17,
            "VAM": GameRender.VAM
        }
        data["game_render"] = GameRender.UNKNOWN # DEFAULT
        for text, render in render_mappings.items():
            if text+" -" in headline_text:
                data["game_render"] = render
                break  # Exit the loop once a match is found

        return data

        