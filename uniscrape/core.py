from .config_manager import ConfigManager
from .crawler import Crawler
from .scraper import Scraper
from .pdf import Pdf

from typing import Optional


class Core:
    def __init__(self, config: ConfigManager, url: Optional[str] = None):
        self.config = config
        self.logger_tool = self.config.logger_tool
        self.logger_print = self.config.logger_print
        self.url = url

    def crawl_and_scrape(self) -> None:
        """
        Performs crawling and scraping.
        """
        crawler = Crawler(self.config)
        # Start crawler
        if crawler.start_crawler(self.url):
            # Configure scraper
            scraper = Scraper(self.config)
            docs = scraper.start_scraper(crawler.get_urls_to_scrap())
            self.logger_tool.info(f"Scraped {docs} documents.")

    def crawl(self) -> None:
        """
        Performs only crawling without scraping.
        """
        crawler = Crawler(self.config)
        crawler.start_crawler(self.url)

    def scrape_local_pdfs(self) -> None:
        """
        Performs scraping downloaded pdfs.
        """
        scraper = Pdf(self.config)
        # Start pdf scraping
        docs = scraper.start_scraper_pdf(self.config.pdfs_to_scrape)
        self.logger_tool.info(f"Scraped {docs} documents.")

    def scrape(self) -> None:
        """
        Performs scraping of urls from url_to_scrape.csv.
        """
        crawler = Crawler(self.config)
        scraper = Scraper(self.config)
        docs = scraper.start_scraper(crawler.get_urls_to_scrap())
        self.logger_tool.info(f"Scraped {docs} documents.")
