import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# Initializing Firestore
cred = credentials.Certificate("key here") # input key for Firebase here
firebase_admin.initialize_app(cred)
db = firebase.client()

def fetch_and_parse(url):
    """Fetches and parses HTML contenct from a given URL."""
    headers = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"Failed to fetch {url}: {response.status_code}")
        return None

def extract_reports_nato():
    """Scrapes NATO Reports."""
    url = "https://www.nato.int/cps/en/natolive/news.htm"
    soup = fetch_and_parse(url)
    if soup:
        reports = []
        for article in soup.find_all('div', class_='news-listing'): # Can Adjust selector as needed
            title = article.find('a').text.strip()
            link = article.find('a')['href']
            date = article.find('span', class_='date').text.strip()
            reports.append({"title":title, "link": link, "date": date, "source": "DoD"})
        return reports
    return []

def store_in_firestore(reports):
    """Stores the scraped reports in Firestore."""
    for report in reports:
        doc_ref = db.collection("reports").document()
        doc_ref.set(report)
        print(f"Stored: {report['title']}")

def main():
    nato_reports = extract_reports_nato()
    dod_reports = extract_reports_dod()
    all_reports = nato_reports + dod_reports
    if all_reports:
        store_in_firestore(all_reports)
    else:
        print("No Reports Found.")

if __name__ == "__main__":
    main()



