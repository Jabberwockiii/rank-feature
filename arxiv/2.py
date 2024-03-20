from playwright.sync_api import sync_playwright
import json
import asyncio

async def crawl_website(url):
    async with sync_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Find all the paper elements
        paper_elements = await page.query_selector_all('p.list-title.is-inline-block')

        # Find all the abstract elements
        abstract_elements = await page.query_selector_all('.abstract-full')

        papers = []

        for i, paper_element in enumerate(paper_elements):
            # Extract the paper ID and URL
            paper_link = await paper_element.query_selector('a')
            paper_url = await paper_link.get_attribute('href')
            paper_id = paper_url.split('/')[-1]

            # Get the corresponding abstract element
            if i < len(abstract_elements):
                abstract_text = await abstract_elements[i].inner_text()
            else:
                abstract_text = ''

            paper_data = {
                'url': paper_url,
                'paper_id': paper_id,
                'abstract': abstract_text
            }

            papers.append(paper_data)

        await browser.close()

        return papers

async def main():
    base_url = 'https://arxiv.org/search/advanced?advanced=&terms-0-term=artificial+intelligence&terms-0-operator=AND&terms-0-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=date_range&date-year=&date-from_date=2023-05-05&date-to_date=2024-02-10&date-date_type=submitted_date&abstracts=show&size=25&order=submitted_date'

    all_papers = []
    max_index = 20000
    step = 25

    async def scrape_page(start_index):
        url = base_url + f'&start={start_index}'
        page_papers = await crawl_website(url)
        return page_papers

    tasks = []
    for start_index in range(0, max_index, step):
        task = asyncio.create_task(scrape_page(start_index))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for page_papers in results:
        all_papers.extend(page_papers)

    # Dump the papers data into a JSON file
    with open('papers-parallel.json', 'w') as file:
        json.dump(all_papers, file, indent=2)

    print(f'Scraped {len(all_papers)} papers and saved to papers.json')

if __name__ == '__main__':
    asyncio.run(main())