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
from typing import Literal


def remove_special_characters(text, special_chars=None) -> str:
    """
    This function removes any unwanted characters and new lines.
    """
    if special_chars is None:
        special_chars = r'[^A-Za-z0-9\s\.,;:\'\"\?\!\-ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]'

    # Removing characters defined above
    text = re.sub(special_chars, '', text)
    # Removing emojis
    text = emoji.replace_emoji(text, replace="")
    # Removing extra new lines to only one new line
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


class MarkdownChat(BaseModel):
    response_text: str = Field(
        ..., description="Clean Markdown, ready for display, paragraphs, content and structure preserved.")


def batch_loader_for_LLM(text, max_chunk_size=5000):
    for i in range(0, len(text), max_chunk_size):
        yield text[i:i+max_chunk_size]


def clean_PDF(text: str, api_key: str) -> str:
    """
    This function is responsible for converting OCR scraped PDF into markdown with LLM help.

    returns:
        str: Formatted string (markdown)
    """
    client = OpenAI(api_key=api_key)

    markdown_parts = []

    for batch in batch_loader_for_LLM(text):
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that helps with document parsing."},
                {"role": "user", "content": f"Convert the following text to markdown:\n{batch}"}
            ],
            response_format=MarkdownChat,
        )
        message = response.choices[0].message
        text = message.parsed.response_text
        markdown_parts.append(text)
        combined = "\n\n".join(markdown_parts)

    return remove_special_characters(combined)


def clean_HTML(html: str) -> str:
    """
    This function is responsible for parsing HTML and converting it to markdown format.

    returns:
        str: Formatted string (markdown) 
    """
    soup = BeautifulSoup(html, "html.parser")

    # Define unwanted html tags
    for tag in soup(["script", "style", "nav", "aside", "footer", "form", "noscript", "iframe", "img"]):
        tag.extract()

    main_content = soup.find("article") or soup.find("main") or soup.body

    # Remove unwanted divs with given length and keywords
    meta_keywords = ['kategorie', 'tags',
                     'language', 'język', 'autor', 'posted in']

    # Getting last five divs
    divs = main_content.find_all('div')[-5:]
    for div in divs:
        t = div.get_text(strip=True).lower()
        if len(t) < 20 and any(k in t for k in meta_keywords):
            div.decompose()

    # Define html2text converter
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.single_line_break = True
    converter.ignore_links = True

    text = converter.handle(str(main_content))

    return remove_special_characters(text)


def get_title_from_url(html: str, url: str) -> str:
    def clean_title(title: str) -> str:
        return title.strip('/').replace('_', ' ').replace('%20', ' ').replace('-', ' ').capitalize()
    if html:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("meta", property="og:title")
        title = title["content"] if title and "content" in title.attrs else urlparse(
            url).path
        return clean_title(title)

    title = os.path.splitext(os.path.basename(urlparse(url).path))[0]
    return clean_title(title)


def get_title_from_pdf(path: str) -> str:
    doc = pymupdf.open(path)
    metadata = doc.metadata
    return metadata.get("title")


def get_institution_from_url(url: str) -> str:
    """
    Extracts the academic or institutional affiliation from a given URL.

    Returns:
    - str: The name of the institution if recognized, otherwise 'Other'.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    keywords = {
        'Poznan University of Technology': 'put.poznan.pl',
        'Warsaw University of Technology': 'pw.edu.pl',
        'System Informacji Prawnej': 'sip.lex.pl'
    }

    for institution, pattern in keywords.items():
        if pattern in netloc:
            return institution

    return 'Other'


class DocumentClassificationResult(BaseModel):
    result_of_classification: Literal['Instruction', 'Article', 'Statute', 'Forms'] = Field(
        ...,
        description=(
            "Final classification of the document into one of the following categories:\n"
            "'Instruction': Practical guidance documents, user manuals, how-tos, or step-by-step procedures.\n"
            "'Article': Informative or academic content such as publications, blog posts, research findings.\n"
            "'Statute': Official policies, rules, regulations, laws, or university resolutions (e.g., uchwaly, regulaminy).\n"
            "'Forms': Templates, application forms, documents meant to be filled out by users."
        ))


def classify_document_with_LLM(text: str, title: str, api_key: str) -> Literal['Instruction', 'Article', 'Statute', 'Forms']:
    """
    Uses LLM to classify a document into a predefined category.

    Returns:
        str: Predicted document class, one of: 'Instruction', 'Article', 'Statute', 'Forms'.
    """
    client = OpenAI(api_key=api_key)
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that helps with document classification."},
            {"role": "user", "content": f"Perform classification. You are given document titled: {title}. \n\n {text}."}
        ],
        response_format=DocumentClassificationResult,
        temperature=0.0
    )
    message = response.choices[0].message
    predicted_class = message.parsed.result_of_classification

    return predicted_class


def classify_document(url: str, title: str, api: str) -> Literal['Instruction', 'Article', 'Statute', 'Forms']:
    """
    Classifies a document based on the URL or, if no match is found, delegates to the LLM classifier.

    First attempts to match specific keywords in the URL for heuristic classification.
    If no keyword matches, it calls `classify_document_with_LLM()` to determine the class using the document content.

    Returns:
        str: Classified document type ('Instruction', 'Article', or 'Statute').
    """
    keywords = {'Article': 'artykul',
                'Instruction': 'instrukcje',
                'Statute': 'regulamin',
                'Statute': 'uchwala',
                'Forms': 'formularz'}

    for key, value in keywords.items():
        if value in url:
            return key

    return classify_document_with_LLM(url, title, api)
