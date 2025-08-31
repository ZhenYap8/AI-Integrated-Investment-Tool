AI Investment Analysis Tool 📈🤖

This repository contains an AI-powered investment analysis platform that scrapes stock market company data and generates actionable insights.
It is built with a FastAPI backend and integrates scraping, data analysis, and AI models to support smarter investment research.

🚀 Features

Company Scraper – Extracts data on listed companies from stock market sources.

AI Insights – Provides AI-generated commentary and recommendations on company performance.

Growth & Market Share Analysis – Tools for evaluating market opportunities (e.g. BCG growth-share matrix).

API Access – FastAPI backend for clean endpoints and integration into other applications.

Investment Reports – Automated generation of structured investment reports.

🛠️ Tech Stack

Backend: FastAPI (Python)

Scraping: Selenium / BeautifulSoup / requests (depending on target sources)

AI Analysis: OpenAI API (LLM-based insights)

Data Handling: Pandas, NumPy

Deployment: Docker / Cloud (optional)

🔧 Installation & Setup

Clone the repo:

git clone https://github.com/yourusername/ai-investment-tool.git
cd ai-investment-tool


Create a virtual environment & install dependencies:

python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

pip install -r requirements.txt


Run the FastAPI server:

uvicorn discovery:app --reload


Open in browser:

http://127.0.0.1:8000/docs

📊 Example Workflow

Use the scraper to fetch company data.

Query the AI analysis endpoint to generate insights.

Export an investment report with AI commentary + financial indicators.

📬 Roadmap

 Add sentiment analysis from financial news

 Expand scraping to multiple exchanges

 Implement portfolio risk analysis

 Deploy as a web app with dashboard

⚖️ License & Credit

This project is copyright © Zhen.

The source code is made public for reference and learning purposes only.

Modification, redistribution, or commercial use is not permitted without explicit permission.

If you use part of this project for research or reference, please credit this repository.
