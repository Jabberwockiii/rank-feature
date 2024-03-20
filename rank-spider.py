import json
import fitz
from playwright.sync_api import sync_playwright
import requests
import io
from datetime import datetime, timedelta
import time

def scrape_data(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

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
        return data

def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        pdf_stream = io.BytesIO(response.content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except fitz.FileDataError as e:
        print(f'Error processing PDF: {pdf_url}')
        print(f'Error message: {str(e)}')
        return ""
    
def process_date(date):
    url = f'https://huggingface.co/papers?date={date}'
    scraped_data = scrape_data(url)
    
    for item in scraped_data:
        try:
            item['link'] = f"https://arxiv.org/pdf{item['link']}.pdf"
            text = extract_text_from_pdf(item['link'])
            item['text'] = text
        except:
            item['text'] = ''
    
    json_data = json.dumps(scraped_data, indent=2)
    
    filename = f'scraped_data_{date}.json'
    with open(filename, 'w') as file:
        file.write(json_data)
    
    print(f'Scraped data for {date} saved to {filename}')
    
    # Add a sleep delay after each date processing
    time.sleep(1)  # Adjust the delay time as needed

# Specify the start and end dates
start_date = datetime(2023, 12, 22)
end_date = datetime(2024, 3, 6)

# Generate the list of dates
dates = []
current_date = start_date
while current_date <= end_date:
    # if that date is sunday or saterday then skip
    try:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    except:
        current_date += timedelta(days=1)

# Scrape data for each date sequentially
for date in dates:
    process_date(date)