"""
Scraper Module

This module contains functions for scraping data from provided URLs.
"""
import logging
import os
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry
from typing import Tuple
import pandas as pd

from config_manager import ConfigManager
import process_text
from utils import package_to_json, create_session, get_timestamp


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger_tool = logging.getLogger('UniScrape_tools')


class Scraper:
    def __init__(self, config_manager: ConfigManager):
        self.config: ConfigManager = config_manager
        self.logger_tool = self.config.logger_tool
        self.logger_print = self.config.logger_print
        self.visited_folder = self.config.visited_url_folder
        self.visited_file = self.config.visited_url_file

    def _scrape_text(self, url: str) -> Tuple[str, str]:
        """
        Performs scraping HTML from site and returns clean text.

        Return:
            str: Cleaned text.
            str: Title of document extracted from link.
        """
        session = create_session(retry_total=1)
        response = session.get(url)

        if response and response.ok:
            cleaned_response = process_text.clean_HTML(response.text)
            title = process_text.process_web_metadata(response.text)
        elif not response:
            self.logger_tool.info(
                f"Empty response: {url}. Response: {response}")
        elif not response.ok:
            self.logger_tool.info(
                f"Error response: {url}. Response: {response.status_code}")

        return cleaned_response, title

    def start_scraper(self, urls_to_scrap: pd.DataFrame) -> int:
        """
        Initiates scraper process, checks if URLs are already scraped, scrapes new URLs, and updates the visited list.

        Return:
            int: Count of scraped documents.
        """
        scraped_count = 0

        if urls_to_scrap.empty:
            self.logger_tool.info("No URLs to scrap.")
            self.logger_print.info("No URLs to scrap.")
            return 0

        visited_urls = self.load_visited_urls()

        try:
            for index, row in urls_to_scrap.iterrows():
                url = row['url']

                if url in visited_urls['url'].values:
                    self.logger_tool.info(
                        f"Skipping already scraped URL: {url}")
                    self.logger_print.info(
                        f"Skipping already scraped URL: {url}")
                    continue

                try:
                    scraped_count += 1
                    self.logger_print.info(
                        f"Scraping at index: {index} -> {url}")
                    self.logger_tool.info(
                        f"Scraping at index: {index} -> {url}")

                    result, title = self._scrape_text(url)
                    date = get_timestamp()
                    json_result = package_to_json(title, result, url, date)
                    print(json_result)

                    visited_urls = pd.concat(
                        [visited_urls, pd.DataFrame({'url': [url]})], ignore_index=True)
                    self.append_to_visited_urls(pd.DataFrame({'url': [url]}))

                except Exception as e:
                    self.logger_tool.error(f"Error scraping {url}: {e}")
                    self.logger_print.error(f"Error scraping {url}: {e}")

        except Exception as e:
            self.logger_tool.error(f"Error in scraper: {e}")
            self.logger_print.error(f"Error in scraper: {e}")

        return scraped_count

    def append_to_visited_urls(self, urls_dataframe: pd.DataFrame, file_name: str = None, folder: str = None, mode='a') -> None:
        if file_name is None:
            file_name = self.visited_file
        if folder is None:
            folder = self.visited_folder

        file_path = os.path.join(folder, file_name)

        os.makedirs(folder, exist_ok=True)

        try:
            write_header = not os.path.exists(file_path) or mode == 'w'
            urls_dataframe.to_csv(file_path, sep='\t', mode=mode,
                                  index=False, encoding='utf-8', header=write_header)

            self.logger_tool.info(
                f"Saved {urls_dataframe.shape} rows to {file_path}")
        except Exception as e:
            self.logger_tool.error(
                f"Error while saving to file: {file_path}: {e}")

    def load_visited_urls(self, file_name: str = None, folder: str = None) -> pd.DataFrame:
        if file_name is None:
            file_name = self.visited_file
        if folder is None:
            folder = self.visited_folder

        file_path = os.path.join(folder, file_name)

        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
                self.logger_tool.info(
                    f"Loaded {df.shape[0]} visited URLs from {file_path}")
                return df
            except Exception as e:
                self.logger_tool.error(
                    f"Error loading visited URLs from {file_path}: {e}")
                return pd.DataFrame(columns=["url"])
        else:
            self.logger_tool.info(
                f"No visited URLs file found, starting fresh.")
            return pd.DataFrame(columns=["url"])
