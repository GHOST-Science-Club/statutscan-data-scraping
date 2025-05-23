"""
Scraper Module

This module contains functions for scraping data from provided URLs.
"""
from .config_manager import ConfigManager
from .utils import package_to_json, create_session, get_timestamp, dump_json
from .database import Database
from .metrics import Analyzer
from .process_text import clean_PDF, clean_HTML, get_title_from_url, get_institution_from_url, classify_document, remove_special_characters, get_all_metadata

import logging
import os
import urllib3
from urllib3.util.retry import Retry
from typing import Tuple
import pandas as pd
import pymupdf
from pdf2image import convert_from_bytes
import easyocr
import numpy as np
import pymupdf4llm
import time


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger_tool = logging.getLogger('UniScrape_tools')


class Scraper:
    def __init__(self, config_manager: ConfigManager):
        self.config: ConfigManager = config_manager
        self.logger_tool = self.config.logger_tool
        self.logger_print = self.config.logger_print
        self.visited_folder = self.config.visited_url_folder
        self.visited_file = self.config.visited_url_file
        self.language = self.config.language
        self.api_key = self.config.openai_api_key
        self.ocr = easyocr.Reader([self.language])
        self.sleep_time = self.config.sleep_time

    def _scrape_text(self, url: str) -> Tuple[str, str]:
        """
        Scrapes HTML from a webpage and extracts clean text.

        Args:
            url (str): URL of the webpage.

        Returns:
            Tuple[str, str]: Extracted title and cleaned text content.
        """
        session = create_session(retry_total=self.config.max_retries)
        response = session.get(url, timeout=10)

        if response and response.ok:
            cleaned_response = clean_HTML(response.text)
            title = get_title_from_url(response.text, url)
        elif not response:
            self.logger_tool.info(
                f"Empty response: {url}. Response: {response}")
            return "", ""
        elif not response.ok:
            self.logger_tool.info(
                f"Error response: {url}. Response: {response.status_code}")
            return "", ""

        return title, cleaned_response

    def _scrape_pdf(self, url: str) -> Tuple[str, str]:
        """
        Extracts text from a PDF file. Uses OCR if the PDF contains images.

        Args:
            url (str): URL of the PDF.

        Returns:
            Tuple[str, str]: Extracted title and text content.
        """

        session = create_session(retry_total=self.config.max_retries)
        response = session.get(url, timeout=10)

        if response and response.ok:
            pdf_bytes = response.content
        elif not response:
            self.logger_tool.info(
                f"Empty response: {url}. Response: {response}")
        elif not response.ok:
            self.logger_tool.info(
                f"Error response: {url}. Response: {response.status_code}")

        text, title = "", ""

        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc)

        except Exception as e:
            self.logger_print.error(f"Error reading PDF with PyMuPDF: {e}")
            self.logger_tool.error(f"Error reading PDF with PyMuPDF: {e}")

        if not text.strip():
            # Use OCR
            self.logger_tool(f"OCR used for PDF: {url}")
            text = self._extract_with_ocr(pdf_bytes)
            cleaned_response = remove_special_characters(
                clean_PDF(text, self.api_key))
        else:
            # Standard scraping
            cleaned_response = remove_special_characters(
                pymupdf4llm.to_markdown(doc))

        title = get_title_from_url(None, url)

        return title, cleaned_response

    def _extract_with_ocr(self, pdf):
        """
        Extracts text from an image-based PDF using OCR.

        Args:
            pdf_bytes (bytes): Byte content of the PDF.

        Returns:
            str: Extracted text.
        """
        try:
            images = convert_from_bytes(pdf)
            reader = self.ocr
            text = "\n".join(" ".join(result[1] for result in reader.readtext(
                np.array(image))) for image in images)

        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return ""

        return text

    def start_scraper(self, urls_to_scrap: pd.DataFrame) -> int:
        """
        Initiates scraper process, checks if URLs are already scraped, scrapes new URLs, and updates the visited list.

        Return:
            int: Count of scraped documents.
        """
        scraped_count = 0
        db = Database(self.config)
        db.connect_to_database()

        if urls_to_scrap.empty:
            self.logger_print.info("No URLs to scrap.")
            return 0

        visited_urls = self.load_visited_urls()
        analyzer = Analyzer(config=self.config)

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
                    self.logger_print.info(
                        f"Scraping at index: {index} -> {url}")
                    self.logger_tool.info(
                        f"Scraping at index: {index} -> {url}")

                    if url.endswith('pdf'):
                        title, result = self._scrape_pdf(url)
                    else:
                        title, result = self._scrape_text(url)

                    if len(result) > self.config.min_text_len:
                        # All metadata and metrics
                        metadata = get_all_metadata(
                            title, result, url, self.config.language, analyzer, self.config)

                        # Pack into JSON
                        json_result = package_to_json(*metadata)
                        self.logger_print.info(dump_json(json_result))
                        scraped_count += 1

                        # Send if database access is True and print in console
                        if self.config.allow_database_connection:
                            db.append_to_database(json_result)
                    else:
                        self.logger_tool.warning(
                            f"Text to short: {len(result)} while minumum is: {self.config.min_text_len}")

                    visited_urls = pd.concat(
                        [visited_urls, pd.DataFrame({'url': [url]})], ignore_index=True)
                    self.append_to_visited_urls(pd.DataFrame({'url': [url]}))

                    # Sleep for a while to avoid being blocked by the server
                    time.sleep(self.sleep_time)

                except Exception as e:
                    self.logger_tool.error(f"Error scraping {url}: {e}")
                    self.logger_print.error(f"Error scraping {url}: {e}")

        except Exception as e:
            self.logger_tool.error(f"Error in scraper: {e}")
            self.logger_print.error(f"Error in scraper: {e}")

        db.close_connection()
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
