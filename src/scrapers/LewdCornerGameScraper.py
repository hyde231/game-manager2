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

class LewdCornerGameScraper(GameScraper):
    name: str = "LewdCorner"
    subdomain: Optional[str] = None
    domain: str = "lewdcorner"
    suffix: str = "com"
    paths: Optional[List[str]] = None
    
    def __init__(self, game_instance: Game, **kwargs):
        self.cookiefile: str = "./data/cookies/lewdcorner_cookies.txt"
        self.headerfile: str = "./data/headers/lewdcorner_headers.json"
        self.base_url = "https://lewdcorner.com"
        super().__init__(game_instance, cookiefile=self.cookiefile, headerfile=self.headerfile, **kwargs)

    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        text, final_url = self.get_text(url, method="cloudscraper")
        if not text:
            return {"url": url, "error": "Failed to fetch data"}

        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        soup = BeautifulSoup(text, "html.parser")
        data: Dict[str, Optional[str]] = {
            "url": final_url,
            "source": LewdCornerGameScraper.name
        }

        try:
            # Title
            title_tag = soup.find("h1", class_="p-title-value")
            if title_tag:
                pure_text_nodes = [child for child in title_tag.children if child.name is None]
                title = ''.join(pure_text_nodes).strip()
                data["title"] = title.split("[")[0].strip()

            # Cover image
            article = soup.find("article", class_="message-body")
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
            description_tag = soup.find("meta", property="og:description")
            if description_tag:
                data["description"] = description_tag.get("content")
            # Better description, if available
            description_div = article.find("script", class_="js-extraPhrases")
            if description_div:
                data["description"] = unescape(description_div.find_parent("div").get_text(strip=True).replace("Overview:",""))

            # Developer
            developer_tag = soup.find('dl', class_="pairs--customField", attrs={"data-field": "Developer"})
            if developer_tag:
                data["developer"] =  developer_tag.find('dd').get_text(strip=True)

            # Version
            version_dl = soup.find("dl", {"data-field": "version"})
            if version_dl:
                data["last_version"] = version_dl.find("dd").text.strip()

            # Last update
            last_update = soup.find("dl", {"data-field": "dateversionrelease"})
            if last_update:
                data["updated"] = parse_date(last_update.find("dd").text.strip()).date().isoformat()

            # Published date
            published = soup.find("dl", {"data-field": "dategamerelease"})
            if published:
                data["published"] = parse_date(published.find("dd").text.strip()).date().isoformat()

            # Language
            language = soup.find("dl", {"data-field": "Language"})
            if language:
                data["language"] = [lang.strip().lower() for lang in language.find("dd").text.split(",")]

            # OS
            os = soup.find("ol", {"data-field": "OS"})
            if os:
                data["os"] = [os_li.text.strip().lower() for os_li in os.find_all("li")]

            # Extract status
            headline = soup.find("h1")
            headline_text = str(headline)
            # Extract Status
            if headline.find("span", string="Completed"):
                data["status"] = GameStatus.COMPLETED
            elif headline.find("span", string="Abandoned"):
                data["status"] = GameStatus.ABANDONED
            elif headline.find("span", string="Onhold"):
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
                if headline.find("span", string=lambda t: t.lower() == text.lower() or t.lower() == f"[{text.lower()}]"):
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
                if headline.find("span", string=lambda t: t.lower() == text.lower() or t.lower() == f"[{text.lower()}]"):
                    data["game_render"] = render
                    break  # Exit the loop once a match is found
            
            # Extract tags
            taglist = soup.find("dl", class_="tagList")
            if taglist:
                data["tags"] = list(set(tag.text.lower().strip() for tag in taglist.find_all("a", class_="tagItem")))
            else:
                print(f"  ERROR: Couldn't find taglist, please check cookies or try again later. Info returned: {data}")
                return data
            # Additional tags in Genres
            genre_tag = soup.find("span", class_="bbCodeSpoiler-button-title", string="Genre:")
            if genre_tag:
                # Traverse upward until reaching the parent <div> with class "bbCodeSpoiler"
                bb_code_spoiler = target_tag.find_parent("div", class_="bbCodeSpoiler")
                if bb_code_spoiler:
                    # Find the <div> with class "bbCodeBlock-content" inside it
                    bb_code_content = bb_code_spoiler.find("div", class_="bbCodeBlock-content")
                    if bb_code_content:
                        # Extract and split the text by ","
                        tags = [tag.strip() for tag in bb_code_content.get_text(strip=True).split(",")]
                        data["tags"] = sorted(list(set(data["tags]"]+tags)))

        except Exception as e:
            data["error"] = f"Error parsing data: {e}"

        return data
