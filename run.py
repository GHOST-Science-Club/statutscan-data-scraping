import argparse
from uniscrape.core import Core
from uniscrape.config_manager import ConfigManager

# Define you settings here
config = ConfigManager(database=False, max_links=30)
url = "https://instrukcje.put.poznan.pl/category/vpn/"


def main():
    parser = argparse.ArgumentParser(
        description="Parameters listed below:"
    )
    parser.add_argument('--crawl_and_scrape', action='store_true',
                        help="Crawl and scrape URLs.")
    parser.add_argument('--pdf', action='store_true',
                        help="Scrape PDF documents.")
    parser.add_argument('--scrape', action='store_true',
                        help='Scrape files or urls from .csv.')
    parser.add_argument('--crawl', action='store_true',
                        help='Crawl only.')
    args = parser.parse_args()

    runner = Core(config=config, url=url)

    if args.crawl_and_scrape:
        runner.crawl_and_scrape()
    elif args.pdf:
        runner.scrape_local_pdfs()
    elif args.scrape:
        runner.scrape()
    elif args.crawl:
        runner.crawl()
    else:
        print(
            "No valid arguments provided. Use --[crawl | crawl_and_scrape | scrape].")


if __name__ == "__main__":
    main()
