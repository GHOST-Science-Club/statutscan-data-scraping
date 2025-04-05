"""
Process Module

This module contains functions for cleaning data and process meta-data from scraped pages.
"""
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import emoji
import pymupdf
import html2text
import os


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
    """
    This function is responsible for parsing HTML and converting it to markdown format.

    returns:
        str: Formatted string (markdown) 
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "aside", "footer", "form", "noscript", "iframe", "a", "img"]):
        tag.extract()

    main_content = soup.find("article") or soup.find("main") or soup.body

    text = html2text.html2text(str(main_content))
    text = remove_special_characters(text)

    return text


def get_title_from_url(html: str, url: str) -> str:
    if html:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("meta", property="og:title")
        return title["content"] if title and "content" in title.attrs else urlparse(url).path

    return os.path.splitext(os.path.basename(urlparse(url).path))[0]


def get_title_from_pdf(path: str) -> str:
    doc = pymupdf.open(path)
    metadata = doc.metadata
    return metadata.get("title")
