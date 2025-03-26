"""
Process Module

This module contains functions for cleaning data and process meta-data from scraped pages.
"""
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import emoji
import pymupdf


def remove_special_characters(text, special_chars=None):
    if special_chars is None:
        special_chars = r'[^A-Za-z0-9\s\.,;:\'\"\?\!\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]'

    text = re.sub(special_chars, '', text)
    text = emoji.replace_emoji(text, replace="")
    return text.strip()


def remove_repeated_substrings(text, pattern=r'\.{2,}'):
    text = re.sub(pattern, '.', text)
    return text.strip()


def remove_extra_spaces(text):
    text = re.sub(r'\b([A-Z]) (\w)', r'\1\2', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+\.', '.', text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    return text.strip()


def preprocess_text(text):
    # Remove special characters
    text = remove_special_characters(text)

    # Remove repeated substrings like dots
    text = remove_repeated_substrings(text)

    # Remove extra spaces between lines and within lines
    text = remove_extra_spaces(text)

    return text.strip()


def clean_HTML(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "aside", "footer", "form", "noscript", "iframe", "a"]):
        tag.extract()

    main_content = soup.find("article") or soup.find("main") or soup.body

    text = main_content.get_text(
        separator=" ", strip=True) if main_content else soup.get_text(separator=" ", strip=True)

    text = preprocess_text(text)

    return text


def process_web_metadata(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("meta", property="og:title")
    title_content = title["content"] if title else "Title not found"

    return title_content


def process_pdf_metadata(path: str) -> str:
    doc = pymupdf.open(path)
    metadata = doc.metadata
    return metadata.get("title")
