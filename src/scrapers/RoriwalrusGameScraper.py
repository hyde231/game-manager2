import re
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from typing import Dict, Iterator, Optional, Any, List
from html import unescape
import string

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.Game import Game

class RoriwalrusGameScraper(GameScraper):
    name: str = "Roriwalrus"
    subdomain: Optional[str] = None
    domain: str = "roriwalrus"
    suffix: str = "com"
    paths: Optional[List[str]] = None
    
    def __init__(self, game_instance: Game, **kwargs):
        self.cookiefile: str = "./data/cookies/roriwalrus_cookies.txt"
        self.headerfile: str = "./data/headers/roriwalrus_headers.json"
        self.base_url = "https://Roriwalrus.com"
        super().__init__(game_instance, cookiefile=self.cookiefile, headerfile=self.headerfile, **kwargs)

    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        if not url.startswith("https://www.roriwalrus.com/index.php?downloads/"):
            return {"url": url, "error": "Url has to start with https://www.roriwalrus.com/index.php?downloads/"}

        text, final_url = self.get_text(url, method="cloudscraper")
        if not text:
            return {"url": url, "error": "Failed to fetch data"}

        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        soup = BeautifulSoup(text, "html.parser")
        data: Dict[str, Optional[str]] = {
            "url": final_url,
            "source": RoriwalrusGameScraper.name
        }

        try:
            # Title
            title_tag = soup.find("h1", class_="p-title-value")
            if title_tag:
                pure_text_nodes = [child for child in title_tag.children if child.name is None]
                title = ''.join(pure_text_nodes).strip()
                # Had to use capwords, as some titles were in all caps :(
                data["title"] = string.capwords(unescape(title.split("[")[0].strip()))

            # Cover image
            article = soup.find("article")
            if article:
                cover = article.find("img")
                if cover:
                    src = cover.get("src")
                    try:
                        data_url = self.get_image(src, width=300, method="cloudscraper")
                        data["cover_img"] = data_url
                    except Exception as e:
                        print(f"Image {src} failed to download. Error: ", e)

            # Description
            # TODO
            description_tag = soup.find("meta", property="og:description")
            if description_tag:
                data["description"] = description_tag.get("content")

            info_tags = soup.find_all('li', {"data-xf-list-type":"ul"})
            if info_tags:
                print(info_tags)
                # Developer
                for tag in info_tags:
                    span = tag.find('span', string="Developer Name ")
                    if span:
                        data["developer"] = tag.get_text(strip=True).replace(span.get_text(strip=True), "").strip()
                        break
                # Version
                for tag in info_tags:
                    span = tag.find('span', string="Version number ")
                    if span:
                        data["last_version"] = tag.get_text(strip=True).replace(span.get_text(strip=True), "").strip()
                        break
                # Language
                for tag in info_tags:
                    span = tag.find('span', string="Language")
                    if span:
                        data["language"] = [os.strip().lower() for os in tag.get_text(strip=True).replace(span.get_text(strip=True), "").split(",")]
                        break
                # OS
                for tag in info_tags:
                    span = tag.find('span', string="OS")
                    if span:
                        data["os"] = [os.strip().lower() for os in tag.get_text(strip=True).replace(span.get_text(strip=True), "").split(",")]
                        break
                    
            
            # Extract status
            headline = soup.find("h1")
            headline_text = str(headline)
            # Extract Status
            if headline.find("span", string="Completed"):
                data["status"] = GameStatus.COMPLETED
            elif headline.find("span", string="Abandoned"):
                data["status"] = GameStatus.ABANDONED
            elif headline.find("span", string="On hold"):
                data["status"] = GameStatus.ONHOLD
            elif headline.find("span", string="Hiatus"):
                data["status"] = GameStatus.ONHOLD
            elif headline.find("span", string="Active"):
                data["status"] = GameStatus.ACTIVE
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
                if headline.find("span", string=lambda t: t.lower() == text.lower() or t.lower() == f"[{text.lower()}]"):
                    data["game_engine"] = engine
                    break  # Exit the loop once a match is found

            # Extract Render Engine
            render_mappings = {
                "AI": GameRender.AI,
                "DAZ": GameRender.DAZ,
                "DAZ3D": GameRender.DAZ,
                "Hand Drawn": GameRender.HAND_DRAWN,
                "HS": GameRender.HS,
                "HS2": GameRender.HS2,
                "Koikatsu": GameRender.KOIKATSU,
                "TK17": GameRender.TK17,
                "VAM": GameRender.VAM
            }
            data["game_render"] = GameRender.UNKNOWN # DEFAULT
            for text, render in render_mappings.items():
                if headline.find("span", string=lambda t: t.lower() == text.lower() or t.lower() == f"[{text.lower()}]"):
                    data["game_render"] = render
                    break  # Exit the loop once a match is found
            
            # Extract tags
            taglist = soup.find("span", class_="js-tagList")
            if taglist:
                data["tags"] = list(set(tag.text.lower().strip() for tag in taglist.find_all("a", class_="tagItem")))
            

        except Exception as e:
            data["error"] = f"Error parsing data: {e}"

        return data
