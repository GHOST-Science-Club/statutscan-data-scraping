"""
PDF Module

This module contains all functions to work with PDFs.
"""
import logging
import pymupdf
from pdf2image import convert_from_path
import easyocr
import numpy as np
import os
import pandas as pd
from typing import Tuple


from config_manager import ConfigManager
from process_text import clean_PDF, process_pdf_metadata
from utils import package_to_json, get_timestamp

logger_tool = logging.getLogger('UniScrape_tools')


class Pdf:
    def __init__(self, config_manager: ConfigManager):
        self.config: ConfigManager = config_manager
        self.logger_tool = self.config.logger_tool
        self.logger_print = self.config.logger_print
        self.visited_pdfs_file = self.config.visited_pdfs_file
        self.visited_pdfs = self.load_visited_pdfs()
        self.ocr_reader = easyocr.Reader(['pl', 'en'], gpu=False)

    def _get_text_from_pdf(self, path: str) -> Tuple[str, str]:
        """
        This function scrapes text from pdf file and extract title.

        Returns:
            str: Title of pdf file.
            str: Content of pdf file.
        """
        doc = pymupdf.open(path)
        text = "\n".join(page.get_text() for page in doc)

        # If no text is recognized, use OCR
        if not text.strip():
            self.logger_tool.warning(f"Using OCR for {path}...")
            text = self._extract_text_with_ocr(path)

        title = process_pdf_metadata(path)
        text = clean_PDF(text=text)

        return title, text

    def _extract_text_with_ocr(self, path: str) -> str:
        """
        This function is responsible to get text from fake pdfs and images. It converts input to image and then use OCR to scrape text.

        Returns:
            str: Scraped text.
        """
        try:
            images = convert_from_path(path, dpi=300)
            extracted_text = []

            for i, img in enumerate(images):
                text = self.ocr_reader.readtext(np.array(img), detail=0)
                extracted_text.append(" ".join(text))
            text = "\n".join(extracted_text)

            return text

        except Exception as e:
            self.logger_tool.error(f"Error for OCR, PDF {path}: {str(e)}")
            return ""

    def start_scraper_pdf(self, folder_path: str) -> int:
        scraped_count = 0

        if not os.path.exists(folder_path):
            self.logger_tool.error(f"Directory {folder_path} not exist.")
            return 0

        try:
            for pdf_name in os.listdir(folder_path):
                if not pdf_name.endswith(".pdf"):
                    continue

                pdf_path = os.path.join(folder_path, pdf_name)

                if pdf_name in self.visited_pdfs["filename"].values:
                    self.logger_tool.info(
                        f"Skipping already scraped pdf: {pdf_name}")
                    self.logger_print.info(
                        f"Skipping already scraped pdf: {pdf_name}")
                    continue

                self.logger_print.info(f"Scraping pdf: {pdf_name}")
                self.logger_tool.info(f"Scraping pdf: {pdf_name}")

                title, text = self._get_text_from_pdf(pdf_path)
                date = get_timestamp()
                json_result = package_to_json(
                    title=title, content=text, source=pdf_name, timestamp=date)
                print(json_result)

                self.append_to_visited_pdfs(pdf_name)
                scraped_count += 1

        except Exception as e:
            self.logger_tool.error(f"Error scraping pdf {pdf_name}: {e}")
            self.logger_print.error(f"Error scraping pdf {pdf_name}: {e}")

        return scraped_count

    def load_visited_pdfs(self) -> pd.DataFrame:
        if os.path.exists(self.visited_pdfs_file):
            return pd.read_csv(self.visited_pdfs_file)
        return pd.DataFrame(columns=["filename"])

    def append_to_visited_pdfs(self, pdf_name: str):
        new_entry = pd.DataFrame({"filename": [pdf_name]})
        self.visited_pdfs = pd.concat(
            [self.visited_pdfs, new_entry], ignore_index=True)
        self.visited_pdfs.to_csv(self.visited_pdfs_file, index=False)
