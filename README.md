⚠️ This project is currently under development. Some features may not work as expected. ⚠️

This is a tool for scraping and processing data from various sources used in RAG project.
See our [app](https://github.com/GHOST-Science-Club/statutscan-app). 

### Installation (for Linux/MacOS)
Ensure you have Python 3.12 installed. Remember to add **OPEN_AI_KEY** and **MONGO_KEY** to .env file.


#### Clone repo and cd into
```
git clone https://github.com/GHOST-Science-Club/statutscan-data-scraping.git
cd statutscan-data-scraping
```

#### Create and activate a virtual environment
```
python3 -m venv venv
source venv/bin/activate 
```

#### Install dependencies and create project structure
```
pip install --upgrade pip
pip install setuptools
pip install .
```

### Run application
Add url you want to scrape and run app:
```
python3 run.py --param
```
Parameters:
- --scrape 
- --pdf
- --crawl
- --crawl_and_scrape

### Structure
```
statutscan-data-scraping/
│-- uniscrape/             # Application source code
│-- to_scrape/             # Folder for files to be scraped
│   ├── urls_to_scrape.csv
│   ├── pdfs/
│-- logs/                 # Application logs
│   ├── app_log.log
│-- visited/              # Visited documents
│-- setup.py              # Installation script
│-- requirements.txt      # List of dependencies
│-- README.md             # Documentation
```
### Uninstallation
```
pip uninstall statutscan-data-scraping
rm -rf venv
```
### Issues
Please add all issues to Issues section on Github.
