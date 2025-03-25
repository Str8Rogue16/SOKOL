import os
import requests
import random
import time
import logging
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initializing Firestore
cred = credentials.Certificate(r"filepath.json")  # input key for Firebase here
firebase_admin.initialize_app(cred)
db = firestore.client()

# Rotating User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Load Country-Specific Sources from .env
COUNTRY_SITES = {
    "RU": os.getenv("RU_SITES", "").split(","),
    "UA": os.getenv("UA_SITES", "").split(","),
    "BY": os.getenv("BY_SITES", "").split(","),
    "PL": os.getenv("PL_SITES", "").split(","),
    "TR": os.getenv("TR_SITES", "").split(","),
    "CSTO": os.getenv("CSTO_SITES", "").split(","),
}

def fetch_and_parse(url):
    """Fetches and parses HTML content from a given URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None

def extract_articles(url):
    """Scrapes news articles from a given site."""
    soup = fetch_and_parse(url)
    if not soup:
        return []

    reports = []
    
    for article in soup.find_all('article'):  # Placeholder, will refine per country
        title = article.find('a').text.strip() if article.find('a') else "No title"
        link = article.find('a')['href'] if article.find('a') else url
        reports.append({"title": title, "link": link, "source": url})

    return reports

def store_in_firestore(reports):
    """Stores the scraped reports in Firestore."""
    for report in reports:
        doc_ref = db.collection("reports").document()
        doc_ref.set(report)
        logging.info(f"Stored: {report['title']}")

def main():
    """Scrapes selected country sources."""
    country = input("Enter country code to scrape (RU, UA, BY, PL, TR): ").strip().upper()

    if country not in COUNTRY_SITES:
        logging.error("Invalid country code! Choose from RU, UA, BY, PL, TR.")
        return

    all_reports = []

    for site in COUNTRY_SITES[country]:
        logging.info(f"Scraping: {site}")
        articles = extract_articles(site)
        all_reports.extend(articles)
        time.sleep(random.randint(2, 5))  # Prevent rate limiting

    if all_reports:
        store_in_firestore(all_reports)
    else:
        logging.warning("No Reports Found.")

if __name__ == "__main__":
    main()
