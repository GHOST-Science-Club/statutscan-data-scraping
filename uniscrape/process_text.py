"""
Process Module

This module contains functions for cleaning data and process meta-data from scraped pages.
"""
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import emoji
import pymupdf


def clean_HTML(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "aside", "footer", "form", "noscript", "iframe", "a"]):
        tag.extract()

    main_content = soup.find("article") or soup.find("main") or soup.body

    text = main_content.get_text(
        separator=" ", strip=True) if main_content else soup.get_text(separator=" ", strip=True)

    text = emoji.replace_emoji(text, replace="")

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()

    return text


def clean_PDF(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?i)strona \d+|page \d+', '', text)
    text = re.sub(r'[•●▪■□▸▹►◄◦→←↓↑⇨]', '', text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    text = emoji.replace_emoji(text, replace="")
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
