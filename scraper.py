from datetime import datetime
from dateutil import parser
import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import logging
import hashlib
from urllib.parse import urljoin

# Load environment variables from .env file (or .sources)
load_dotenv(".sources")

# Initialize Firebase
cred = credentials.Certificate(r".json") # Certificate filepath goes here
firebase_admin.initialize_app(cred)
db = firestore.client()

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Helper to extract image URLs even from lazy-loaded images
def extract_image_url(image_tag, base_url):
    if not image_tag:
        return None

    # Prioritize lazy-loaded attributes first
    for attr in ['data-src', 'data-lazy-src', 'srcset', 'src']:
        if image_tag.has_attr(attr):
            url = image_tag[attr]
            if attr == 'srcset':
                url = url.split()[0]  # use the first URL in srcset
            return urljoin(base_url, url)
        
    return None

# Function to fetch and parse HTML content asynchronously
async def fetch_and_parse(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                return BeautifulSoup(html, 'html.parser')
            else:
                logging.error(f"Failed to fetch {url}: {response.status}")
                return None
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

# Function to scrape content from Kyiv Independent
async def scrape_kyivindependent(session, url):
    logging.info(f"🔍 Scraping: {url}")
    soup = await fetch_and_parse(session, url)

    if soup:
        reports = []
        base_url = "https://kyivindependent.com"

        for card in soup.find_all('article', class_='tagCard'):
            title_tag = card.find('h2', class_='tagCard__title')
            title = title_tag.find('a').text.strip() if title_tag and title_tag.find('a') else "No title"
            link = title_tag.find('a')['href'] if title_tag and title_tag.find('a') else url
            full_link = urljoin(base_url, link)

            # Extract date
            date_tag = card.find('time')
            if date_tag and date_tag.has_attr('datetime'):
                iso_date = date_tag['datetime']
                try:
                    published_at = datetime.strptime(iso_date, "%Y-%m-%d").strftime("%B %d, %Y")
                except ValueError:
                    published_at = "Unknown Date"
            else:
                published_at = "Unknown Date"

            # Extract image
            img_tag = card.find("img")
            image_url = extract_image_url(img_tag, base_url) if img_tag else "/static/noimage.png"

            # Append report
            reports.append({
                "title": title,
                "link": full_link,
                "date": published_at,
                "source": "Kyiv Independent",
                "image_url": image_url
            })

        if reports:
            logging.info(f"📦 Storing {len(reports)} reports...")
            store_in_firestore(reports)
        else:
            logging.warning(f"⚠️ No reports found on {url}")
    else:
        logging.warning(f"⚠️ Soup was None for {url}")

# Function to scrape content from TASS RU
async def scrape_tass(session, url):
    logging.info(f"🇷🇺 Scraping: {url}")
    soup = await fetch_and_parse(session, url)

    if soup:
        reports = []
        base_url = "https://tass.ru"

        # Select all article cards from homepage layout
        for article in soup.select('a.tass_pkg_card_wrapper-r-hZB'):
            try:
                link = article.get('href')
                full_link = urljoin(base_url, link)

                title_tag = article.select_one('span.tass_pkg_title-xVUT1')
                if not title_tag:
                    continue
                title = title_tag.text.strip()

                # TASS doesn't show clear dates in this layout, so we'll timestamp it as "scraped now"
                published_at = datetime.now().strftime("%B %d, %Y")

                # No images in this layout, fallback to placeholder
                image_url = "/static/noimage.png"

                reports.append({
                    "title": title,
                    "link": full_link,
                    "date": published_at,
                    "source": "TASS",
                    "image_url": image_url
                })
            except Exception as e:
                logging.warning(f"❌ Failed to parse a TASS article block: {e}")
                continue

        if reports:
            logging.info(f"📦 Storing {len(reports)} reports from TASS...")
            store_in_firestore(reports)
        else:
            logging.warning(f"⚠️ No articles found on TASS page {url}")
    else:
        logging.warning("⚠️ TASS soup is None.")

# Function to scrape content from RIA Novosti's Defense & Safety section.
async def scrape_ria(session, url):
    logging.info(f"🇷🇺 Scraping RIA: {url}")
    soup = await fetch_and_parse(session, url)

    if soup:
        reports = []
        base_url = "https://ria.ru"

        for article in soup.select("div.list-item"):
            title_tag = article.select_one("a.list-item__title")
            if not title_tag:
                continue

            title = title_tag.text.strip()
            link = title_tag["href"]
            full_link = urljoin(base_url, link)

            # Date
            date_tag = article.select_one("div.list-item__date")
            published_at = date_tag.text.strip() if date_tag else "Unknown Date"

            # Image
            img_tag = article.find("img")
            image_url = extract_image_url(img_tag, base_url) if img_tag else "/static/noimage.png"

            reports.append({
                "title": title,
                "link": full_link,
                "date": published_at,
                "source": "RIA Novosti",
                "image_url": image_url
            })

        if reports:
            logging.info(f"📦 Storing {len(reports)} RIA articles...")
            store_in_firestore(reports)
        else:
            logging.warning(f"⚠️ No articles found on RIA page: {url}")
    else:
        logging.warning("⚠️ RIA soup is None.")

# Store scraped reports in Firestore
def store_in_firestore(reports):
    for report in reports:
        doc_id = hashlib.md5(f"{report['title']}{report['link']}".encode('utf-8')).hexdigest()
        doc_ref = db.collection("reports").document(doc_id)
        try:
            doc_ref.set(report)
            logging.info(f"Stored: {report['title']}")
        except Exception as e:
            logging.error(f"Failed to store report: {report['title']} - {e}")

# Main scraping function
async def scrape_sites():
    kyiv_sites = os.getenv("KYIVINDEPENDENT_SITES", "").split(",")
    tass_sites = os.getenv("TASS_SITES", "").split(",")
    ria_sites = os.getenv("RIA_SITES", "").split(",")   
   
    async with aiohttp.ClientSession() as session:
        tasks = []

        for url in kyiv_sites:
            if url.strip():
                tasks.append(scrape_kyivindependent(session, url.strip()))
        
        for url in tass_sites:
            if url.strip():
                tasks.append(scrape_tass(session, url.strip()))

        for url in ria_sites:
            if url.strip():
                tasks.append(scrape_ria(session, url.strip()))

        await asyncio.gather(*tasks)

# Entry point
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scrape_sites())

if __name__ == "__main__":
    main()
