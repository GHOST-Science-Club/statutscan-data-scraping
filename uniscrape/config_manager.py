"""
Config Manager Module

This module is responsible for configuration and settings used in this project.
"""
import logging
import os
from dotenv import load_dotenv


class ConfigManager:
    """
    A configuration manager for setting up and managing settings for a crawler and scraper.
    """

    def __init__(self, print_to_console: bool = True, log_level=logging.INFO, database: bool = False, sleep_time: float = 3,
                 max_links: int = 10, minimum_text_length: int = 100, max_retries: int = 2, dataset_language: str = 'pl'):
        """
        Initializes ConfigManager with default or overridden settings.

        Parameters
            print_to_console: Flag to enable or disable printing logs in console.
            log_level: Logging level.
            database: Flag to enable or disable sending scraped content to database.
            sleep_time: Time between requests.
            max_links: Maximum links to be crawled (TEMPORARY).
            max_retries: How much retries we allow in request.
            dataset_language: Default language of scraped websites.
        """
        # Configurables
        self.sleep_time = sleep_time
        self.maximum_links_to_visit = max_links
        self.allow_database_connection = database
        self.language = dataset_language
        self.min_text_len = minimum_text_length
        self.max_retries = max_retries

        # API
        load_dotenv()
        self.database_api_key = os.getenv('MONGO_KEY')
        self.openai_api_key = os.getenv('OPEN_AI_KEY')

        if not self.database_api_key:
            self.logger_tool.error(
                "MongoDB API key (MONGO_KEY) not found in environment variables.")

        if not self.openai_api_key:
            self.logger_tool.error(
                "OpenAI API key (OPEN_AI_KEY) not found in environment variables.")

        if not self.database_api_key or not self.openai_api_key:
            raise RuntimeError(
                "One or more required API keys are missing. Check environment variables.")

        # Directories
        self.visited_url_folder = "visited/"
        self.visited_url_file = "visited_urls.csv"
        self.url_to_scrape_folder = "to_scrape/"
        self.url_to_scrape_file = "urls_to_scrape.csv"
        self.pdfs_to_scrape = "to_scrape/pdfs/"
        self.visited_pdfs_file = "visited/visited_pdfs.csv"

        # Logger
        self.logs_folder = "logs/"
        self.logs_file = "app_log.log"

        self.print_to_console = print_to_console
        self.logger_print = self.setup_logger_print(print_to_console)

        self.logs_path = os.path.join(self.logs_folder, self.logs_file)
        self.logger_print.info(f"Logs are saved in: {self.logs_path}")

        self.logger_tool = self.setup_logger_tool(self.logs_path, log_level)

        # Initialization of logger
        self.logger_tool.info(20*"*")
        self.logger_tool.info(
            "*** UniScrape - crawler and scraper for University sites ***")

    @staticmethod
    def setup_logger_tool(log_file_path: str, log_level):
        logger_tool = logging.getLogger('UniScrape_tools')
        logger_tool.setLevel(log_level)

        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        if not logger_tool.hasHandlers():
            logger_tool.addHandler(file_handler)

        formatter = logging.Formatter(
            '%(asctime)s: %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)

        logger_tool.addHandler(file_handler)
        return logger_tool

    @staticmethod
    def setup_logger_print(enable_print: bool):
        logger_print = logging.getLogger('UniScrape_print')
        logger_print.setLevel(logging.INFO)

        if enable_print:
            console_handler = logging.StreamHandler()
        else:
            console_handler = logging.NullHandler()

        formatter = logging.Formatter('| %(message)s')
        console_handler.setFormatter(formatter)
        logger_print.addHandler(console_handler)
        return logger_print
