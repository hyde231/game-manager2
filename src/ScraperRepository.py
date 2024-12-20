from typing import Type, List, Optional
import tldextract

class ScraperRepository:
    """
    A repository to manage and retrieve scraper classes based on URL or name.
    """

    def __init__(self):
        """
        Initialize an empty scraper repository.
        """
        self.repository: List[Type['GameScraper']] = []

    def add(self, scraper_class: Type['GameScraper']) -> None:
        """
        Add a scraper class to the repository.

        Parameters:
            scraper_class (Type[GameScraper]): The scraper class to add.
        """
        self.repository.append(scraper_class)

    def get_scraper_by_url(self, url: str) -> Optional[Type['GameScraper']]:
        """
        Retrieve a scraper class that matches the given URL.

        Parameters:
            url (str): The URL to find a matching scraper for.

        Returns:
            Optional[Type[GameScraper]]: The matching scraper class, or None if not found.
        """
        tld_info = tldextract.extract(url)
        for scraper_class in self.repository:
            # Check domain and suffix match
            if tld_info.domain != scraper_class.domain or tld_info.suffix != scraper_class.suffix:
                continue

            # Check subdomain match if specified in scraper_class
            if getattr(scraper_class, 'subdomain', None):
                if tld_info.subdomain != scraper_class.subdomain:
                    continue

            # Check if paths are specified and match
            if getattr(scraper_class, 'paths', None):
                if not any(path in url for path in scraper_class.paths):
                    continue

            return scraper_class  # Found matching scraper_class

        return None

    def get_scraper_by_name(self, name: str) -> Optional[Type['GameScraper']]:
        """
        Retrieve a scraper class by its name.

        Parameters:
            name (str): The name of the scraper.

        Returns:
            Optional[Type[GameScraper]]: The scraper class with the matching name, or None if not found.
        """
        for scraper_class in self.repository:
            if scraper_class.name == name:
                return scraper_class
        return None
