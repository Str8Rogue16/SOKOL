from collections import defaultdict
from flask import Flask, jsonify, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firestore
cred = credentials.Certificate(r"filepath.json") # file path to credentials
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def index():
    """Fetches reports from Firestore, groups by country and date, and serves the HTML page."""
    reports_ref = db.collection("reports")
    docs = reports_ref.stream()

    reports_by_country = defaultdict(lambda: defaultdict(list))  # {country: {date: [reports]}}
    
    for doc in docs:
        report = doc.to_dict()
        country = report.get("country", "Unknown")
        date = report.get("date", "Unknown Date")
        reports_by_country[country][date].append(report)

    return render_template("index.html", reports_by_country=reports_by_country)

@app.route('/get_reports', methods=['GET'])
def get_reports():
    """Fetches reports from Firestore."""
    reports_ref = db.collection("reports")
    docs = reports_ref.stream()

    reports = []
    for doc in docs:
        reports.append(doc.to_dict())

    return jsonify(reports)

@app.route('/filter_reports', methods=['GET'])
def filter_reports():
    country = request.args.get('country')
    date = request.args.get('date')

    reports_ref = db.collection("reports")
    docs = reports_ref.stream()

    filtered_reports = []

    for doc in docs:
        report = doc.to_dict()
        if (country and report.get('country') == country) and (date and report.get('date') == date):
            filtered_reports.append(report)

    return render_template('index.html', reports=filtered_reports)

if __name__ == '__main__':
    app.run(debug=True)
