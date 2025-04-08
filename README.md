# SOKOL

AI-Powered Predictive Analytics

Utilization of ML models to detect patterns in certain activity around the globe in near real time. 

To be conducted in phases: 
1. Data Collection Pipeline
Sources: OSINT feeds, news APIs, Twitter, Telegram, government reports, and academic papers.
Scraping & Ingestion: Web scraping, API access, and real-time feeds.
  - Currently utilizing Websites to collect information from.
  - Next step is to integrate flagged twitter accounts to start pulling tweets into the database.
  - Third will be attempting to connect Telegram to the database and start collecting information from various channels.
  - Fourth will be to start collecting government reports based off the various events around the globe. Currently focused on Russian and Ukraine conflict but will evolve into a more global effort.
  - Lastly will be the collection of academic papers accessible via the internet based off of various topics such as oil, natural gas, gold, precious minerals, etc.
    
2. Database: Store structured/unstructured data (PostgreSQL for structured data, Firestore for real-time updates).
  - Whichever will be most costeffective and ability to expand depending on how large the project gets. 

3. Machine Learning & AI Models
 - NLP for Threat Detection: Use models like BERT/GPT for analyzing text from news and social media.
 - Time-Series Analysis: Predict patterns in activity based on historical trends.
 - Graph Analysis: Map relationships between geopolitical actors, events, and risks.

4. Visualization & Alerts
 - Dashboard with Interactive Maps: Show real-time hotspots of potential threats.
 - Automated Alerts & Reports: Trigger alerts based on AI-detected risks.
