
from dataclasses import dataclass, field, asdict
import datetime

from src.ScraperRepository import ScraperRepository
from src.GameScraper import GameScraper
from src.Game import Game
from src.GameList import GameList

from src.scrapers.AllTheFallenGameScraper import AllTheFallenGameScraper
# from src.scrapers.DikgamesGameScraper import DikgamesGameScraper
from src.scrapers.F95zoneGameScraper import F95zoneGameScraper
from src.scrapers.FapNationGameScraper import FapNationGameScraper
from src.scrapers.LewdCornerGameScraper import LewdCornerGameScraper
from src.scrapers.RoriwalrusGameScraper import RoriwalrusGameScraper


repository = ScraperRepository()
repository.add(AllTheFallenGameScraper)
# repository.add(DikgamesGameScraper)
repository.add(F95zoneGameScraper)
repository.add(FapNationGameScraper)
repository.add(LewdCornerGameScraper)
repository.add(RoriwalrusGameScraper)

gamelist = GameList(repository=repository)
gamelist.load()

for game in gamelist.games:
    print(f"Tags for {game.title}: {game.tags}")
    game.tags = sorted(list(set(
        [t.lower() for t in game.tags]
    )))
    print(f"Tags for {game.title}: {game.tags}")
    print("")

gamelist.save()
gamelist.create_index()