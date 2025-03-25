"""
Config Manager Module

This module is responsible for configuration and settings used in this project.
"""
import logging
import os


class ConfigManager:
    def __init__(self, print_to_console: bool = True, log_level=logging.INFO):
        self.sleep_time = 2
        self.maximum_links_to_visit = 5

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
