from playwright.sync_api import sync_playwright
import json

def crawl_website(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        # Find all the paper elements
        paper_elements = page.query_selector_all('p.list-title.is-inline-block')

        papers = []

        for paper_element in paper_elements:
            # Extract the paper ID and URL
            paper_link = paper_element.query_selector('a')
            paper_url = paper_link.get_attribute('href')
            paper_id = paper_url.split('/')[-1]

            # Find the corresponding abstract element
            abstract_element = paper_element.query_selector('following-sibling::span.abstract-full.has-text-grey-dark.mathjax')

            if abstract_element:
                abstract_text = abstract_element.inner_text()
            else:
                abstract_text = ''

            paper_data = {
                'url': paper_url,
                'paper_id': paper_id,
                'abstract': abstract_text
            }

            papers.append(paper_data)

        browser.close()

        return papers

def main():
    base_url = 'https://arxiv.org/search/advanced?advanced=&terms-0-term=artificial+intelligence&terms-0-operator=AND&terms-0-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=date_range&date-year=&date-from_date=2023-05-05&date-to_date=2024-02-10&date-date_type=submitted_date&abstracts=show&size=25&order=submitted_date'

    start_index = 0
    all_papers = []

    while True:
        url = base_url + f'&start={start_index}'
        page_papers = crawl_website(url)

        if not page_papers:
            break

        all_papers.extend(page_papers)
        start_index += 25

        with open('arxiv_badcase.json', 'w') as file:
            json.dump(all_papers, file, indent=2)

    print(f'Scraped {len(all_papers)} papers and saved to papers.json')

if __name__ == '__main__':
    main()