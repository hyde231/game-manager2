import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Union, Any
from jinja2 import Environment, FileSystemLoader

from src.JsonStorage import JsonStorage
from src.ScraperRepository import ScraperRepository
from src.Game import Game

class GameList:
    """
    A class to manage a list of Game objects, providing methods to add, update,
    retrieve, and persist games, as well as generate an HTML index.
    """

    def __init__(self, repository: ScraperRepository, config_file: str = "data\gamelist.json"):
        """
        Initialize the GameList.

        Parameters:
            repository (ScraperRepository): The repository containing available scrapers.
            config_file (str): The path to the Config JSON file.
        """
        self.games: List[Game] = []
        self.repository = repository
        
        with open(config_file, 'r', encoding='utf-8') as file:
            self.config = json.load(file)

        self.storage = JsonStorage(self.config["data_file"])

    def has(self, title: str) -> bool:
        """
        Check if a Game with the given title exists in the Game list.

        Parameters:
            title (str): The title to search for.

        Returns:
            bool: True if a Game with the title exists, False otherwise.
        """
        return any(title.lower() in game.title.lower() for game in self.games)
    
    def get_by_id(self, id:str) -> Optional[Game]:
        return next((game for game in self.games if game.id == id), None)
        
    def get_by_title(self, title: str, criteria: Optional[Dict[str,Any]] = None) -> Optional[Game]:
        """
        Retrieve a Game by its title and optional criteria.

        Parameters:
            title (str): The title to search for.
            criteria (Optional[Dict[str, Any]]): Additional criteria to match.

        Returns:
            Optional[Game]: The matching Game, or None if not found.
        """
        unique_default = object() # to distinguish between missing attributes and attributes with None values. This ensures that if an attribute is missing, the comparison will fail, and the Game will be skipped.
        for game in self.games:
            if title.lower() in game.title.lower():
                if not criteria:
                    return game
                if all(getattr(game, key, unique_default) == value for key, value in criteria.items()):
                    return game
        return None

    def get_by_url(self, url: str) -> Optional[Game]:
        """
        Retrieve a Game by its URL.

        Parameters:
            url (str): The URL to search for.

        Returns:
            Optional[Game]: The matching Game, or None if not found.
        """
        for game in self.games:
            if url == game.url:
                return game
        return None

    def add(self, game: Game) -> None:
        """
        Add a new game to the list if it doesn't already exist.

        Parameters:
            game (Game): The game to add.

        Returns:
            None
        """
        if self.has(game.title):
            print(f"'{game.title}' by {game.developer} is already in Gamelist")
        else:
            self.games.append(game)

    def update_or_create(self, game: Game) -> Optional[Game]:
        """
        Update an existing game or create a new one if it doesn't exist.

        Parameters:
            game (Game): The game to update or create.

        Returns:
            Game: The updated or newly added game.
        """
        existing_game = self.get_by_title(game.title, {"developer":game.developer, "source":game.source})
        if not existing_game:
            print(f"Game with title '{game.title}' by {game.developer} not found. Adding it.")
            self.games.append(game)
            return game
        existing_game.from_dict(game.to_dict())
        return existing_game
        
    def add_game_from_url(self, url: str, properties: Optional[Dict[str, Any]] = None, **kwargs) -> Game:
        """
        Create a new game from a URL and add it to the list.

        Parameters:
            url (str): The URL of the game to add.
            properties (Optional[Dict[str, Any]]): Additional properties for the game.
            **kwargs: Additional parameters for scraping.

        Returns:
            Game: The newly added game.
        """
        # Using mutable objects (like lists and dicts) as default arguments can introduce bugs because any changes to these objects persist across function calls.
        if properties is None:
            properties = {}
        overwrite = False if properties else True  # If properties are given, don't overwrite them
        game = Game(url=url)
        
        game.update(repository=self.repository, immediate_update=True, overwrite=overwrite, **kwargs)
        
        self.update_or_create(game)
        return game

    def load(self) -> None:
        """
        Load the games from the JSON storage.

        Returns:
            None
        """
        self.games = self.storage.load(Game)
        print(f"Loaded {len(self.games)} games")
        self.apply_patches()
        print(f"Patches applied")

    def save(self) -> None:
        """
        Save the games to the JSON storage.

        Returns:
            None
        """
        self.storage.save( self.to_dict() )
        print(f"Saved {len(self.games)} games")

    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convert the list of games to a list of dictionaries.

        Returns:
            List[Dict[str, Any]]: The list of game dictionaries.
        """
        gamelist = [game.to_dict() for game in self.games]
        return sorted(gamelist, key=lambda x: x['title'])

    def create_index(self, base_dir: str = "./") -> None:
        """
        Generate a static HTML index of the games.

        Parameters:
            base_dir (str): The base directory to save the index file.
            archive_root_dir (str): The root directory of the archive (with one folder for each game with a matching name, within each a Screenshot folder)

        Returns:
            None
        """
        print(f"Creating html index in {base_dir}")
        env = Environment(loader=FileSystemLoader('./assets/'))
        template = env.get_template('gameindex.template.html')
        data = {
            'title': "Index",
            'heading': "GameList Index",
            'games': self.to_dict()
        }

        for game in data["games"]:
            game["images"] = get_image_filenames( os.path.join( self.config["archive_root"], game["archive_folder"] or game["title"], "Screenshots" ) )

        html_content = template.render(data)
        file_name = "gameindex.html"
        path = os.path.join(base_dir,file_name)

        try:
            with open(path, "w", encoding='utf-8') as file:
                file.write(html_content)
            print(f"Index created successfully at {path}")
        except IOError as e:
            print(f"Error writing file {path}: {e}")
        
        # Optional: Uncomment if you have static assets to copy
        # import shutil
        # print(f"  INFO: Copy assets")
        # shutil.copy("gameindex.css", base_dir)
        # shutil.copy("gameindex.js", base_dir)

    def check_for_updates(self, immediate_update=False) -> List[Game]:
        """
        Check all games for updates and optionally update them.

        Parameters:
            immediate_update (bool): Whether to update games immediately if updates are found.
            **kwargs: Additional parameters for checking updates.

        Returns:
            List[Game]: A list of games that were updated.
        """
        updates = []
        for game in self.games:
            print(f"  Checking '{game.title}' by {game.developer}                                                                           ", end='\r')
            try:
                data = game.check_for_updates(repository=self.repository)
                if data and immediate_update:
                    updates.append(game)
                    print(f"    Updating '{game.title}' by {game.developer}")
                    game.update(
                        repository=self.repository,
                        data=data
                    )
                    self.update_or_create(game)
            except Exception as e:
                print(f"    Update of {game.title} failed. Error: {e}")
        print()
        return updates

    def update_all(self) -> None:
        """
        Update all games.

        Parameters:

        Returns:
        """
        updates = []
        for game in self.games:
            print(f"    Updating '{game.title}' by {game.developer}")
            try:
                game.update(repository=self.repository)
                self.update_or_create(game)
            except Exception as e:
                print(f"    Update of {game.title} failed. Error: {e}")
        print()

    def apply_patches(self, patch_file: Optional[str] = None):
        filename = patch_file or self.config["patch_file"]
        with open(filename, 'r', encoding='utf-8') as file:
            patches = json.load(file)
        for patch in patches:
            if patch["id"]:
                game = self.get_by_id(patch["id"])
                if game:
                    if hasattr(game, patch["key"]):  # Ensure the attribute exists
                        setattr(game, patch["key"], patch["value"])


def get_image_filenames(game_dir, image_extensions=['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
    image_files = []
    if not Path(game_dir).is_dir():
        print(f"No files found for {game_dir}")
        return []

    for dirpath, _, filenames in os.walk(game_dir):
        for file in filenames:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(dirpath, file)
                image_files.append(full_path)
    
    # Sort files by modification date (oldest first)
    # Creation date is not reliable on Windows !!
    image_files.sort(key=lambda x: os.path.getmtime(x))

    # FIXME this is ugly  ???
    image_files = [ "file:///" + i.replace('\\', '/').replace(' ', '%20').replace("'","%27") for i in image_files ]

    return image_files