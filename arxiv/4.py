from playwright.sync_api import sync_playwright
import json

MAX_RETRIES = 3

def crawl_website(url, retry_count=0):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)

            # Find all the paper elements
            paper_elements = page.query_selector_all('p.list-title.is-inline-block')
            # Find all the abstract elements
            abstract_elements = page.query_selector_all('.abstract-full')
            authors_elements = page.query_selector_all('.authors')
            titles_elements = page.query_selector_all('p.title ')
            papers = []
            for i, paper_element in enumerate(paper_elements):
                # Extract the paper ID and URL
                paper_link = paper_element.query_selector('a')
                paper_url = paper_link.get_attribute('href')
                paper_id = paper_url.split('/')[-1]
                # Extract the submitted date
                submitted_date_element = page.query_selector('p.is-size-7')
                submitted_date = ''
                if submitted_date_element:
                    submitted_date_text = submitted_date_element.inner_text()
                    submitted_date = submitted_date_text.split(';')[0].replace('Submitted', '').strip()

                if i < len(abstract_elements):
                    abstract_text = abstract_elements[i].inner_text()
                    paper_authors = authors_elements[i].inner_text()[9:]
                    # change the string to list
                    paper_authors = paper_authors.split(',')
                    title = titles_elements[i].inner_text()
                else:
                    abstract_text = ''

                paper_data = {
                    'url': paper_url,
                    'paper_id': paper_id,
                    'abstract': abstract_text,
                    'title': title,
                    'date': submitted_date,
                    'authors': paper_authors
                }
                papers.append(paper_data)

            browser.close()

            return papers
    except Exception as e:
        print(f"Error occurred during crawling: {str(e)}")
        if retry_count < MAX_RETRIES:
            print(f"Retrying (attempt {retry_count + 1})...")
            return crawl_website(url, retry_count + 1)
        else:
            print("Max retries exceeded. Returning empty list.")
            return []

def main():
    base_url = 'https://arxiv.org/search/advanced?advanced=&terms-0-term=artificial+intelligence&terms-0-operator=AND&terms-0-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=date_range&date-year=&date-from_date=2023-09-28&date-to_date=2024-03-10&date-date_type=submitted_date&abstracts=show&size=100&order=submitted_date'

    start_index = 0 
    all_papers = []

    while True:
        url = base_url + f'&start={start_index}'
        page_papers = crawl_website(url)

        if not page_papers:
            break

        all_papers.extend(page_papers)
        start_index += 100 

    # Dump the papers data into a JSON file
        with open('badcase-full-41-s.json', 'w') as file:
            json.dump(all_papers, file, indent=2)

    print(f'Scraped {len(all_papers)} papers and saved to papers.json')

if __name__ == '__main__':
    main()