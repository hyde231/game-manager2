# Game Scraper and Organizer

This project is a Python-based tool designed to scrape, organize, and manage information about games from various online sources. It provides functionality to automate the collection of game data, including titles, developers, tags, and other metadata, and organizes it into a structured format for easy access and updates.
Features

-   Game Scraping: Automatically scrape detailed game information from multiple websites using specialized scraper classes.
-   Game Management: Maintain a collection of games with features to add, update, and search using a robust GameList class. 
-   Customizable Storage: Save and load game data using a JSON storage backend.
-   Interactive Filtering and Display: Generate HTML indexes for easy browsing of game collections, with support for sorting, filtering, and pagination.
-   Tag Handling: Dynamically map and translate tags to user-defined categories for better organization.
-   Pluggable Scrapers: Easily extend support for new websites by implementing custom scraper classes.
-   CLI and Web Integration: Use the functionality in scripts or integrate it into web applications using Flask.

## Installation

Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

Create virtual environment (e.g. venv)

Install dependencies
```bash
pip install -r requirements.txt
```

I personally use it in VSCode with Jupyter extensions installed, so that I can run the ipcnb file directly from there

