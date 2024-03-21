import os
import json
import re
import time
from multiprocessing import Pool
from playwright.sync_api import sync_playwright, TimeoutError, Error

# Get the list of JSON files in the current directory
json_files = [file for file in os.listdir('.') if file.endswith('.json')]

# Initialize an empty list to store the paper IDs
paper_ids = []

# Iterate through each JSON file
new_links = []

def extract_abstract(url, paper_id, retry_count=3, retry_delay=5):
    for attempt in range(retry_count):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, timeout=30000)  # Set a timeout of 30 seconds
                abstract = page.query_selector('p').inner_text()
                title = page.query_selector('h1').inner_text()

                # Extract authors
                author_elements = page.query_selector_all('div.relative span.inline-block span.contents a')
                authors = [element.inner_text() for element in author_elements]

                # Extract date
                date_element = page.query_selector('div.mb-6.flex.flex-wrap.items-center.gap-x-2.text-sm.text-gray-500.sm\\:text-base.md\\:mb-8 div')
                date = date_element.inner_text() if date_element else ''
                date = date[13:]
                # convert the date to date object
                browser.close()
                return abstract, title, authors, date
        except (TimeoutError, Error) as e:
            print(f"Error occurred: {str(e)}")
            if attempt < retry_count - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping this URL.")
                return None

def process_item(item):
    link = item.get('link', '')
    match = re.search(r'https://arxiv\.org/pdf/(\d+\.\d+)\.pdf', link)
    if match:
        paper_id = match.group(1)
        target_url = f"https://huggingface.co/papers/{paper_id}"
        abstract, title, authors, date = extract_abstract(target_url, paper_id)
        return {'url': target_url, 'paper_id': paper_id, 'abstract': abstract, 'title': title, 'authors': authors, 'date': date}
    return None

with Pool() as pool:
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            results = pool.map(process_item, data)
            new_links.extend(filter(None, results))
            print("running")

with open('goodcase-p.json', 'w') as f:
    json.dump(new_links, f, indent=4)

print("Paper IDs extracted and dumped to 'paper_ids.json' successfully.")