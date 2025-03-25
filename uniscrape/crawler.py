"""
Crawler Module

Crawler module is responsible for crawling through website and collect urls.
"""
from config_manager import ConfigManager
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import pandas as pd
import os

from utils import create_session


class Crawler:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger_tool = config_manager.logger_tool
        self.logger_print = config_manager.logger_print
        self.sleep_time = config_manager.sleep_time
        self.maximum_links = config_manager.maximum_links_to_visit
        self.folder = config_manager.url_to_scrape_folder
        self.file_name = config_manager.url_to_scrape_file

    def _normalize_url(self, url: str):
        """
        This function is responsible for normalizing urls to avoid double scraping.

        Returns:
            str: Normalized url.
        """
        parsed = urlparse(url)
        return parsed.scheme + "://" + parsed.netloc + parsed.path

    def start_crawler(self, starting_url: str) -> bool:
        """
        This function is responsible for crawling websites with respect to self.maximum_links and saving visited urls.

        Returns:
            bool: True if crawling ended with no errors, False otherwise.
        """
        visited_urls = set()
        urls_to_visit = [starting_url]

        self.logger_print.info(f"Crawler will start in 5 seconds...")
        time.sleep(5)
        self.logger_tool.info("Crawler started.")

        while urls_to_visit and len(visited_urls) < self.maximum_links:
            url = urls_to_visit.pop(0)
            normalized_url = self._normalize_url(url)
            if normalized_url in visited_urls:
                self.logger_tool.info(
                    f"Already visited url, skip: {normalized_url}")
                continue

            try:
                session = create_session()
                response = session.get(url)

                if response.status_code != 200:
                    self.logger_tool("Response not 200")
                    continue

                visited_urls.add(normalized_url)
                self.logger_tool.info(f"Added url: {url}")

                # Find urls on current website
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    normalized_full_url = self._normalize_url(full_url)
                    if normalized_full_url.startswith(starting_url) and normalized_full_url not in visited_urls:
                        urls_to_visit.append(full_url)

                time.sleep(self.sleep_time)

            except Exception as e:
                self.logger_print.error(f"Error when crawling: {e}")

        self.save_links_to_file(visited_urls)
        return True

    def save_links_to_file(self, links, folder: str = None, file_name: str = None):
        if file_name is None:
            file_name = self.file_name
        if folder is None:
            folder = self.folder

        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, file_name)

        df = pd.DataFrame(list(links), columns=["url"])
        df.to_csv(path, index=False)

    def get_urls_to_scrap(self) -> pd.DataFrame:
        path = os.path.join(self.folder, self.file_name)
        file = pd.read_csv(path)
        return file
