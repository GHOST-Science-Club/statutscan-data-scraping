from config_manager import ConfigManager
from crawler import Crawler
from scraper import Scraper
from pdf import Pdf

import logging
import argparse

config = ConfigManager(
    print_to_console=True
)

logger_tool = logging.getLogger('UniScrape_tools')

url = "https://put.poznan.pl/regulaminy"


def crawl_and_scrape():
    crawler = Crawler(config_manager=config)
    # Start crawler
    if crawler.start_crawler(url):
        # Configure scraper
        scraper = Scraper(config_manager=config)
        docs = scraper.start_scraper(crawler.get_urls_to_scrap())
        config.logger_tool.info(f"Scraped {docs} documents.")


def crawl():
    crawler = Crawler(config_manager=config)
    crawler.start_crawler(url)


def scrape_local_pdfs() -> None:
    scraper = Pdf(config_manager=config)
    # Start pdf scraping
    docs = scraper.start_scraper_pdf(config.pdfs_to_scrape)
    config.logger_tool.info(f"Scraped {docs} documents.")


def scrape() -> None:
    crawler = Crawler(config_manager=config)
    scraper = Scraper(config_manager=config)
    docs = scraper.start_scraper(crawler.get_urls_to_scrap())
    config.logger_tool.info(f"Scraped {docs} documents.")


def main():
    parser = argparse.ArgumentParser(
        description="Crawl and scrape or scrape PDFs.")
    parser.add_argument('--crawl_and_scrape', action='store_true',
                        help="Crawl and scrape URLs.")
    parser.add_argument('--pdf', action='store_true',
                        help="Scrape PDF documents.")
    parser.add_argument('--scrape', action='store_true',
                        help='Scrape files or urls from .csv')
    parser.add_argument('--crawl', action='store_true',
                        help='Crawl only')
    args = parser.parse_args()

    if args.crawl_and_scrape:
        crawl_and_scrape()
    elif args.pdf:
        scrape_local_pdfs()
    elif args.scrape:
        scrape()
    elif args.crawl:
        crawl()
    else:
        print("No valid arguments provided. Use --crawl or --pdf.")


if __name__ == "__main__":
    main()
