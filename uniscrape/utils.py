"""
Utils Module

This module contains utility functions for this project.
"""
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime


def package_to_json(title: str, content: str, source: str, institution: str, timestamp: datetime, language: str, type_of_document: str, metrics: dict) -> dict:
    data = {
        "metadata": {
            "title": title,
            "date": timestamp,
            "source": source,
            "institution": institution,
            "language": language,
            "type": type_of_document,
            "metrics": metrics
        },
        "content": content
    }

    return data


def dump_json(json_file: dict) -> str:
    return json.dumps(json_file, ensure_ascii=False, indent=4)


def create_session(retry_total: bool | int = 3, retry_backoff: float = 3.0, verify: bool = False) -> requests.Session:
    """
        Creates and configures a new session with retry logic for HTTP requests.

        This function initializes a `requests.Session` object and sets up a retry mechanism. It configures the session to retry up to three times with a
        backoff factor to control the delay between retries. Handles both HTTP and HTTPS requests.

        The function also ensures that SSL certificate verification is disable for the session.

        Return:
            requests.Session: A configured session object with retry logic.
        """
    session = requests.Session()
    retry = Retry(total=retry_total, backoff_factor=retry_backoff)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.verify = verify
    return session


def get_timestamp() -> datetime:
    """
        Creates timestamp.

        Returns:
            datetime: timestamp in format YYYY-MM-DD HH-MM-SS eg. 2025-03-25 21:37:35
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
