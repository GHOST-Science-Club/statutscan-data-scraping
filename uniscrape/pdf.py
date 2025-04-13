"""
PDF Module

This module contains all functions to work with PDFs.
"""
from .config_manager import ConfigManager
from .process_text import clean_PDF, get_title_from_pdf
from .utils import package_to_json, get_timestamp, dump_json
from .database import Database

import logging
import pymupdf
from pdf2image import convert_from_path
import easyocr
import numpy as np
import os
import pandas as pd
from typing import Tuple
import spacy
import re


logger_tool = logging.getLogger('UniScrape_tools')


class Pdf:
    def __init__(self, config_manager: ConfigManager):
        self.config: ConfigManager = config_manager
        self.logger_tool = self.config.logger_tool
        self.logger_print = self.config.logger_print
        self.visited_pdfs_file = self.config.visited_pdfs_file
        self.visited_pdfs = self.load_visited_pdfs()
        self.ocr_reader = easyocr.Reader(['pl', 'en'])
        self.nlp = spacy.load("pl_core_news_sm")

    def _get_text_from_pdf(self, path: str) -> Tuple[str, str]:
        """
        This function scrapes text from pdf file and extract title.

        Returns:
            str: Title of pdf file.
            str: Content of pdf file.
        """
        doc = pymupdf.open(path)
        text = "\n".join(page.get_text().strip() for page in doc)

        # If no text is recognized, use OCR
        if not text.strip():
            self.logger_tool.warning(f"Using OCR for {path}...")
            text = self._extract_text_with_ocr(path)

        title = get_title_from_pdf(path)
        text = clean_PDF(text, self.config.openai_api_key)

        return title, text
    
    def _get_institution_name_from_pdf(self,title: str,text: str) -> str:
        """
        This function extracts institution name from pdf title and text.

        Returns:
            str: Institution name.
        """
        institution_name = None
        text = re.sub(r"[\n\r]"," ",text).strip()
        text_stripped = re.sub(r"\s+", ' ',text)
        doc = self.nlp(text_stripped)
        places = []  #(place_name,start_index,start_char,place_name_lem)

        for ent in doc.ents:
            if ent.label_ == 'placeName':
                place_index = ent.start_char
                start_index=place_index-70
                if place_index-70<0:
                    start_index=0
                places.append((ent.text,start_index,ent.start_char))

        # regex_start = r"(?:szkoł{1,3}|uniwersytet[a-z]?|uczelni\w{0,3}|akademi[a-z]?|instytut|wydział|zakład|katedra|technikum|liceum|zesp(?:ó|o)[a-z]{1,3}|zespół szkół|politechni(?:k|c)[a-z]|wyższ[a-z]{1,2})"
        regex_school_number = r"([XIVL]{1,7}\s)?"
        regex_school_type = r"(?:szkoła|uniwersytet|uczelnia|akademi[a-z]?|instytut|wydział|zakład|katedra|technikum|liceum|zesp(?:ó|o)[a-z]{1,3}|zespół szkół|politechni(?:k|c)[a-z]|wyższ[a-z]{1,2})"
        regex_start = rf"{regex_school_number}{regex_school_type}"

        for (place_name,start_ind,start_char_place) in places:

            text_to_analyse = text_stripped[start_ind:start_char_place+len(place_name)]

            regex_combined_1 = rf"STATU(?:T|C).*\s+({regex_start}.*{place_name})" # school name often comes after "STATUT"
            regex_combined_2 = rf"{regex_start}.*{place_name}"
            
            result_1 = re.search(regex_combined_1,text_to_analyse,re.IGNORECASE )
            result_2 = re.search(regex_combined_2, text_to_analyse, re.IGNORECASE ) 
            
            if result_1:
                institution_name_statut = result_1.group(1) # Extracting only school name
            if result_2: 
                institution_name = result_2.group()
                break
            
        return institution_name if institution_name is not None else institution_name_statut
            

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
        db = Database(self.config)
        db.connect_to_database()

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
                institution_name = self._get_institution_name_from_pdf(title,text)
                self.logger_print.info(f"\n Scraped Institution name is {institution_name}")

                date = get_timestamp()

                json_result = package_to_json(
                    title=institution_name, content=text, source=pdf_name, timestamp=date,language=self.config.language, metrics={})

                # Send if database acces is True and print in console
                self.logger_print.info(dump_json(json_result))
                if self.config.allow_database_connection:
                    db.append_to_database(json_result)

                self.append_to_visited_pdfs(pdf_name)
                scraped_count += 1

        except Exception as e:
            self.logger_tool.error(f"Error scraping pdf {pdf_name}: {e}")
            self.logger_print.error(f"Error scraping pdf {pdf_name}: {e}")

        db.close_connection()
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
