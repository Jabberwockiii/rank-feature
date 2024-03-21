import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
                browser.close()
                return abstract
        except (TimeoutError, Error) as e:
            print(f"Error occurred: {str(e)}")
            if attempt < retry_count - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping this URL.")
                return None

def process_url(item):
    link = item.get('link', '')
    match = re.search(r'https://arxiv\.org/pdf/(\d+\.\d+)\.pdf', link)
    if match:
        paper_id = match.group(1)
        target_url = f"https://huggingface.co/papers/{paper_id}"
        abstract = extract_abstract(target_url, paper_id)
        return {'url': target_url, 'paper_id': paper_id, 'abstract': abstract}
    return None

with ThreadPoolExecutor() as executor:
    futures = []
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            for item in data:
                futures.append(executor.submit(process_url, item))

    for future in as_completed(futures):
        result = future.result()
        if result:
            new_links.append(result)
            print("Running")
        with open('paper_ids-parallel.json', 'w') as f:
            json.dump(new_links, f, indent=4)

# Dump the paper IDs to a new JSON file

print("Paper IDs extracted and dumped to 'paper_ids.json' successfully.")