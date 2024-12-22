import os
import re
import json
import uuid
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

import requests

from src.enums.GameStatus import GameStatus
from src.enums.GameEngine import GameEngine
from src.enums.GameRender import GameRender
from src.GameScraper import GameScraper
from src.ScraperRepository import ScraperRepository
from src.Utility import dict_merge, slugify

@dataclass
class Game:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""  # Now properly defined
    title: str = ""
    description: str = ""
    developer: str = ""
    source: str = ""
    url_is_valid: bool = False
    watch: bool = True
    cover_img: str = ""
    versions: dict = field(default_factory=dict)
    published: str = ""
    last_version: str = ""
    updated: str = ""
    os: List[str] =  field(default_factory=list)
    language: List[str] =  field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    my_tags: List[str] = field(default_factory=list)
    my_comment: str = ""
    my_rating: str = ""
    game_engine: Optional[GameEngine] = None
    game_render: Optional[GameRender] = None
    status: Optional[GameStatus] = None

    def __post_init__(self):
        """
        Perform post-initialization processing:
        - Set url_is_valid to True if url is provided.
        """
        
        # Set URL validity
        if self.url:
            # FIXME Skipping actual URL reachability check for simplicity
            # self.url_is_valid = is_url_reachable(self.url)  # too complicated as it would need to handle cookies, logins etc
            self.url_is_valid = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the game instance to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the Game.
        """
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()  # Convert to ISO 8601 string
            if isinstance(value, Enum):
                data[key] = str(value)
        return data

    def from_dict(self, obj: Dict[str, Any], skip_id: bool = True, overwrite: bool = True) -> None:
        """
        Update the Game instance from a dictionary.

        Parameters:
            obj (Dict[str, Any]): The data dictionary.
            skip_id (bool): Whether to skip updating the 'id' field.
            overwrite (bool): Whether to overwrite existing values.

        Returns:
            None
        """
        for key, value in obj.items():
            if key == "id" and skip_id:
                continue
            if key == "status" and value:
                value = GameStatus(value)  # Convert string back to enum
            elif key == "game_engine" and value:
                value = GameEngine(value)  # Convert string back to enum
            elif key == "graphic_engine" and value:
                value = GameRender(value)  # Convert string back to enum
            if hasattr(self, key):
                current_value = getattr(self, key)
                if overwrite or not current_value:
                    setattr(self, key, value)

    def get_scraper(self, repository: ScraperRepository, name: Optional[str] = "") -> Optional[GameScraper]:
        """
        Retrieve the appropriate scraper for the game's URL from the repository.

        Parameters:
            repository (ScraperRepository): The repository containing available scrapers.

        Returns:
            Optional[GameScraper]: The scraper class for the URL, or None if not found.
        """
        if name:
            return repository.get_scraper_by_name(name)    
        if self.url:
            return repository.get_scraper_by_url(self.url)
        return None

    def get_data(self, repository: ScraperRepository):
        #print(f"Scrape info for {self.name}")
        data = {}

        scraper_class = self.get_scraper(repository=repository)
        if not scraper_class:
            print(f"Scraper not found for URL: {self.url}")
            return None

        scraper_instance = scraper_class(self)
        data = scraper_instance.get_data(self.url)

        if not data:
            print(f"No data retrieved for '{self.title}' during update.")
            return None

        return data

    def check_for_updates(
        self,
        repository: ScraperRepository,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Check if there are updates available for the game.

        Parameters:
            repository (ScraperRepository): The repository containing available scrapers.
            **kwargs: Additional options for scraping.

        Returns:
            Optional[Dict[str, Any]]: The new data if updates are found, or None otherwise.
        """
        if not self.url_is_valid:
            #print(f"URL is marked as invalid for '{self.title}'. Aborting update check.")
            return None

        scraper_class = self.get_scraper(repository=repository)
        if not scraper_class:
            print(f"Scraper not found for URL: {self.url}")
            return None

        scraper_instance = scraper_class(self)
        data = scraper_instance.get_data(self.url)
        if not data:
            print(f"Scraper returned no data for URL: {self.url}")
            return None

        updated_date = data.get("updated", "")
        if updated_date and updated_date != self.updated:
            print(f"There is an update with a newer date available for '{self.title}' at {self.url}. Date of {updated_date} vs stored {self.updated}")
            print(f"{type(updated_date)} vs {type(self.updated)}")
            return data

        return None

    def update(
        self,
        repository: ScraperRepository,
        overwrite: Optional[bool] = True,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update the game by scraping new data or using provided data.

        Parameters:
            repository (ScraperRepository): The repository containing available scrapers.
            overwrite (Optional[bool]): Whether to overwrite existing data.
            data (Optional[Dict[str, Any]]): Pre-fetched data to use for the update.
            **kwargs: Additional options for updating and scraping.

        Returns:
            Optional[Dict[str, Any]]: The updated data dictionary, or None if update failed.
        """
        if not self.url_is_valid:
            print(f"URL is marked as invalid for '{self.title}'. Aborting update.")
            return None

        if not data:
            data = self.get_data(repository=repository)

        #print(data)
        self.from_dict(data, overwrite=overwrite)

        if self.published and not self.updated:
            self.updated = self.published

        if self.last_version and self.updated and self.last_version not in self.versions:
            self.versions[self.last_version] = self.updated

        self.tags = sorted(list(set(self.tags)))

        self.set_my_tags()

        return data

    def set_my_tags(self) -> None:
        """
        Set 'my_tags' based on 'tags' and a tag translation file.
        Updates the translation file with any new tags found.
        """
        my_tags = set(self.my_tags)
        filename = './data/tag_translation.json'

        try:
            with open(filename, 'r', encoding='utf-8') as file:
                translation = json.load(file)
        except FileNotFoundError:
            translation = {}

        new_tags_found = False

        for tag in self.tags:
            tag_lower = tag.lower()
            translated_tags = translation.get(tag_lower, [])
            if tag_lower in translation:
                my_tags.update(filter(None, translated_tags))
            else:
                new_tags_found = True
                print(f"New tag found: {tag_lower}")
                translation[tag_lower] = []

        if new_tags_found:
            # TODO backup before overwriting
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('{\n')
                items = sorted(translation.items(), key=lambda x: x[0])
                for idx, (key, value) in enumerate(items):
                    # Serialize the key and value
                    json_key = json.dumps(key, ensure_ascii=False)
                    json_value = json.dumps(sorted(value), ensure_ascii=False)
                    # Write the key-value pair
                    file.write(f'    {json_key}: {json_value}')
                    # Add a comma if it's not the last item
                    if idx < len(items) - 1:
                        file.write(',\n')
                    else:
                        file.write('\n')
                file.write('}\n')

        self.my_tags = sorted(list(my_tags))


def is_url_reachable(url, timeout=5):
    """
    Checks if a URL is reachable.

    Parameters:
        url (str): The URL to check.
        timeout (int): The maximum time to wait for a response.

    Returns:
        bool: True if the URL is reachable, False otherwise.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        status_code = response.status_code
        if 200 <= status_code < 400:
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        print(f"Timeout when trying to reach URL: {url}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Connection error when trying to reach URL: {url}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False