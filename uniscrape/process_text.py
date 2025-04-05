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
from openai import OpenAI
from pydantic import BaseModel, Field


class MarkdownChat(BaseModel):
    response_text: str = Field(
        ..., description="Clean Markdown, ready for display, paragraphs, content and structure preserved.")


def remove_special_characters(text, special_chars=None):
    if special_chars is None:
        special_chars = r'[^A-Za-z0-9\s\.,;:\'\"\?\!\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]'

    text = re.sub(special_chars, '', text)
    text = emoji.replace_emoji(text, replace="")
    return text.strip()


def clean_PDF(text: str, api_key: str) -> str:
    """
    This function returns content from PDFs in markdown. It is using LLM to parse text.
    """
    client = OpenAI(api_key=api_key)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system",
                   "content": "You are helpful assistant that helps with document parsing."},
                  {"role": "user",
                   "content": f"Convert given text to markdown: {text}"}],
        response_format=MarkdownChat
    )

    message = response.choices[0].message
    text = message.parsed.response_text
    return remove_special_characters(text)


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
