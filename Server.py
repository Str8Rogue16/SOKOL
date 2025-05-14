import os
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
import asyncio
from scraper import scrape_sites  # Import the scrape_sites function from scraper.py

# Load environment variables
load_dotenv(".sources")

# Initialize Flask app
app = Flask(__name__)

# Firebase setup
cred = credentials.Certificate(".json") # Firebase Token goes here

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
else:
    # Optionally, you can initialize the app with a name if you want multiple apps
    firebase_admin.initialize_app(cred, name="sokolApp")

db = firestore.client()

def format_report_data(report_data):
    """Ensure image and date formatting fallbacks."""
    # Handle missing images
    if not report_data.get('image_url'):
        report_data['image_url'] = "/static/noimage.png"

    # Handle date formatting or fallback
    published_at = report_data.get('published_at')
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at)
            report_data['published_at'] = dt.strftime("%B %d, %Y")
        except Exception:
            report_data['published_at'] = "Unknown Date"
    else:
        report_data['published_at'] = "Unknown Date"

    return report_data

@app.route("/")
def index():
    """Route to display all reports grouped by country and date"""
    try:
        reports = db.collection('reports').stream()
        reports_by_country = defaultdict(lambda: defaultdict(list))

        for report in reports:
            report_data = format_report_data(report.to_dict())
            country = report_data.get('source', 'Unknown')
            date = report_data.get('date', 'Unknown Date')
            reports_by_country[country][date].append(report_data)

        return render_template('index.html', reports_by_country=reports_by_country)

    except Exception as e:
        return f"An error occurred while fetching reports: {e}"

@app.route("/get_reports")
def get_reports():
    try:
        reports_ref = db.collection('reports').order_by("date", direction=firestore.Query.DESCENDING).limit(100)
        reports = [format_report_data(doc.to_dict()) for doc in reports_ref.stream()]
        return jsonify(reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/filter_reports', methods=['GET'])
def filter_reports():
    """Route to filter reports based on country and date"""
    country = request.args.get('country')
    date = request.args.get('date')

    try:
        reports = db.collection('reports').stream()
        filtered_reports = defaultdict(lambda: defaultdict(list))

        for report in reports:
            report_data = format_report_data(report.to_dict())
            report_country = report_data.get('source', 'Unknown')
            report_date = report_data.get('date', 'Unknown Date')

            if (country and report_country != country) or (date and report_date != date):
                continue

            filtered_reports[report_country][report_date].append(report_data)

        return render_template('index.html', reports_by_country=filtered_reports)

    except Exception as e:
        return f"An error occurred while fetching filtered reports: {e}"

@app.route("/scrape")
async def scrape():
    """Route to trigger scraping and update the reports in Firebase"""
    try:
        # Run the scraper asynchronously
        await scrape_sites()
        return jsonify({"message": "Scraping started and will be completed in the background."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
