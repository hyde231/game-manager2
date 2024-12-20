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

class F95zoneGameScraper(GameScraper):
    name: str = "F95zone"
    subdomain: Optional[str] = None
    domain: str = "f95zone"
    suffix: str = "to"
    paths: Optional[List[str]] = None

    def __init__(self, game_instance: Game, **kwargs):
        self.cookiefile: str = "./data/cookies/f95_cookies.txt"
        self.headerfile: str = "./data/headers/f95_headers.json"
        self.base_url = "https://f95zone.to"
        super().__init__(game_instance, cookiefile=self.cookiefile, headerfile=self.headerfile, **kwargs)

    def get_data(self, url: str) -> Dict[str, Optional[str]]:
        (text, url) = self.get_text(url, method="request")
        if not text:
            return {"url": url, "error": "Failed to fetch data"}
            
        soup = BeautifulSoup(text, "html.parser")

        #with open("page_debug.html", "w", encoding="utf-8") as file:
        #    file.write(text)

        data: Dict[str, Optional[str]] = {
            "url": url,
            "source": F95zoneGameScraper.name
        }

        # Find the article with class "message-body"
        article = soup.find("article", class_=lambda c: c and "message-body" in c.split())
        if not article:
            return {"url": url, "error": "Could not find the main content"}

        # Extract information
        try:
            # Title
            title_tag = soup.find("h1", class_="p-title-value")
            if title_tag:
                # Extract the raw text of the <h1> tag
                raw_title = title_tag.get_text(separator=" ", strip=True)  # Use a space as separator for child tags

                # Remove content enclosed in [] at the end (e.g., [optional version] [optional developer])
                cleaned_title = re.sub(r"\s*\[.*?\]\s*$", "", raw_title)

                # Remove content in <a> and <span> tags by removing their text from the start
                for child in title_tag.find_all(["a", "span"]):
                    child_text = child.get_text(strip=True)
                    if child_text in cleaned_title:
                        cleaned_title = cleaned_title.replace(child_text, "", 1).strip()

                # Replace HTML entities with their actual characters
                cleaned_title = unescape(cleaned_title)

                data["title"] = cleaned_title

            # Release date
            release_date_tag = article.find("b", string="Release Date")
            if release_date_tag and release_date_tag.next_sibling:
                #print(f"Published: {release_date_tag.next_sibling}")
                data["published"] = parse_date(release_date_tag.next_sibling.replace(":"," ").strip()).date().isoformat()

            # Update date
            update_date_tag = article.find("b", string="Thread Updated")
            if update_date_tag and update_date_tag.next_sibling:
                #print(f"Updated: {release_date_tag.next_sibling}")
                data["updated"] = parse_date(update_date_tag.next_sibling.replace(":"," ").strip()).date().isoformat()

            # Developer name
            developer_tag = article.find("b", string="Developer")
            # Check if the next sibling is an <a> tag
            if developer_tag.find_next_sibling("a"):
                data["developer"] = developer_tag.find_next_sibling("a").text.strip()
            elif developer_tag and developer_tag.next_sibling:
                data["developer"] = developer_tag.next_sibling.replace(":"," ").strip()

            # Version
            version_tag = article.find("b", string="Version")
            if version_tag and version_tag.next_sibling:
                data["last_version"] = version_tag.next_sibling.replace(":"," ").strip()

            # OS
            os_tag = article.find("b", string="OS")
            if os_tag and os_tag.next_sibling:
                data["os"] = [os.strip().lower() for os in os_tag.next_sibling.replace(":"," ").split(",")]

            # Languages
            language_tag = article.find("b", string="Language")
            if language_tag and language_tag.next_sibling:
                data["language"] = [lang.strip().lower() for lang in language_tag.next_sibling.replace(":"," ").split(",")]

            # Canonical URL
            canonical_url = soup.find("link", rel="canonical")
            if canonical_url:
                data["url"] = canonical_url.get("href")

            # Description
            description_tag = soup.find("meta", property="twitter:description")
            if description_tag:
                data["description"] = description_tag.get("content")

            # Better Description if available
            # FIXME Doesn't work, yet
            overview_tag = article.find("b", string="Overview")
            if overview_tag:
                # Get the parent <div>
                parent_div = overview_tag.find_parent("div")
                if parent_div:
                    # Replace <br> tags with space
                    for br in parent_div.find_all("br"):
                        br.replace_with(" ")
                    
                    # Extract the cleaned text
                    data["description"] = parent_div.get_text(strip=True)

            # Cover image
            cover = article.find("div", {"aria-label":"Zoom"})
            if cover:
                src = cover.get("data-src")
                #print(f"image src: {src}")
                try:
                    data_url = self.get_image(src, width=300)
                    data["cover_img"] = data_url
                except Exception as e:
                    print(f"Image {src} failed to download. Error: ",e)

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

            # F95 Tags
            data["tags"] = [ tag.text.lower().strip() for tag in soup.find_all("a", class_= "tagItem") ]
            # Author's / Uploader's tags
            # Find the <b>Genre</b> tag
            genre_tag = article.find("b", string="Genre")
            if genre_tag:
                # Find the next sibling div with class "bbCodeSpoiler"
                spoiler_div = genre_tag.find_next_sibling("div", class_="bbCodeSpoiler")
                if spoiler_div:
                    # Find the nested <div class="bbCodeBlock-content">
                    content_div = spoiler_div.find("div", class_="bbCodeBlock-content")
                    if content_div:
                        # Get the text content, split by "," and strip whitespace
                        tags = [tag.strip() for tag in content_div.get_text().split(",")]
                        # Append these tags to data["tags"]
                        if "tags" not in data:
                            data["tags"] = []
                        data["tags"].extend(tags)
            data["tags"] = sorted(data["tags"])

        except Exception as e:
            print(f"Error parsing data from article: {e}")

        return data

    def get_main_thread(self, name, **kwargs) -> Dict[str, Any]:
        def waitfunction(driver):
            return WebDriverWait(driver,30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,".formSubmitRow-controls > button"))).click()

        (text, url) = self.get_text(url, method="chromedriver", arguments=["--headless=new"], wait=waitfunction)
        soup = BeautifulSoup(text, "html.parser")

        cleaned_name = name.lower().replace(" ","").replace("'","").replace(".","").replace("&","")
        for search_result in soup.find_all("h3", class_="contentRow-title"):
            href = search_result.find("a")["href"]
            if cleaned_name in href.replace("-",""):
                # FIXME: The search does not always return the intended game thread. There should be an option to manually check and select
                print(f"  INFO: Thread found at: {href} ")
                url = self.base_url + href
                return url
            
        print(f"  F95: No thread found for {name}!")
        return None
