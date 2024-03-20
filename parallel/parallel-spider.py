import json
import concurrent.futures
import fitz
from playwright.sync_api import sync_playwright
import requests
import io
from datetime import datetime, timedelta
import time
import os

def scrape_data(url, date):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        # Save the HTML content to a file
        html_dir = 'html_files'
        os.makedirs(html_dir, exist_ok=True)
        html_file = os.path.join(html_dir, f'{date}.html')
        with open(html_file, 'w', encoding='utf-8') as file:
            file.write(page.content())

        browser.close()

def extract_text_from_pdf(pdf_url):
    def download_pdf(url):
        response = requests.get(url)
        return io.BytesIO(response.content)

    def extract_text(pdf_stream):
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_pdf = executor.submit(download_pdf, pdf_url)
        pdf_stream = future_pdf.result()

        future_text = executor.submit(extract_text, pdf_stream)
        text = future_text.result()

    return text

def process_date(date):
    html_dir = 'html_files'
    html_file = os.path.join(html_dir, f'{date}.html')

    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)

        data = []
        articles = page.query_selector_all('article')
        for article in articles:
            title = article.query_selector('h3').inner_text().strip()
            link = article.query_selector('h3 a').get_attribute('href')
            upvote = article.query_selector('div.leading-none').inner_text().strip()

            item = {
                'title': title,
                'link': link[7:],
                'upvote': upvote,
            }
            data.append(item)

        browser.close()

    for item in data:
        item['link'] = f"https://arxiv.org/pdf{item['link']}.pdf"
        text = extract_text_from_pdf(item['link'])
        item['text'] = text

    json_data = json.dumps(data, indent=2)

    filename = f'scraped_data_{date}.json'
    with open(filename, 'w') as file:
        file.write(json_data)

    print(f'Scraped data for {date} saved to {filename}')

    # Add a sleep delay after each date processing
    time.sleep(1)  # Adjust the delay time as needed

# Specify the start and end dates
start_date = datetime(2023, 6, 6)
end_date = datetime(2024, 3, 6)

# Generate the list of dates
dates = []
current_date = start_date
while current_date <= end_date:
    # Skip Sundays and Saturdays
    if current_date.weekday() not in [5, 6]:
        dates.append(current_date.strftime("%Y-%m-%d"))
    current_date += timedelta(days=1)

# Scrape HTML files for each date sequentially
for date in dates:
    url = f'https://huggingface.co/papers?date={date}'
    scrape_data(url, date)

# Process the scraped HTML files for each date sequentially
for date in dates:
    process_date(date)