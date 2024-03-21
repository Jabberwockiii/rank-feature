from playwright.async_api import async_playwright
import asyncio
import json

async def crawl_website(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Find all the paper elements
        paper_elements = await page.query_selector_all('p.list-title.is-inline-block')

        # Find all the abstract elements
        abstract_elements = await page.query_selector_all('.abstract-full')
        authors_elements = await page.query_selector_all('.authors')

        papers = []
        for i, paper_element in enumerate(paper_elements):
            # Extract the paper ID and URL
            paper_link = await paper_element.query_selector('a')
            paper_url = await paper_link.get_attribute('href')
            paper_id = paper_url.split('/')[-1]

            # Extract the submitted date
            submitted_date_element = await page.query_selector('p.is-size-7')
            submitted_date = ''
            if submitted_date_element:
                submitted_date_text = await submitted_date_element.inner_text()
                submitted_date = submitted_date_text.split(';')[0].replace('Submitted', '').strip()

            # Extract the paper authors
            if i < len(abstract_elements):
                abstract_text = await abstract_elements[i].inner_text()
                paper_authors = await authors_elements[i].inner_text()
                paper_authors = paper_authors[9:] if paper_authors.startswith('Authors:') else paper_authors
            else:
                abstract_text = ''
                paper_authors = ''

            paper_data = {
                'url': paper_url,
                'paper_id': paper_id,
                'abstract': abstract_text,
                'date': submitted_date,
                'authors': paper_authors
            }

            papers.append(paper_data)

        await browser.close()

        return papers

async def main():
    base_url = 'https://arxiv.org/search/advanced?advanced=&terms-0-term=artificial+intelligence&terms-0-operator=AND&terms-0-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=date_range&date-year=&date-from_date=2023-05-05&date-to_date=2024-02-10&date-date_type=submitted_date&abstracts=show&size=25&order=submitted_date'

    all_papers = []
    max_index = 20000
    step = 25
    max_concurrent_tasks = 64 

    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def scrape_page(start_index):
        async with semaphore:
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
    with open('badcase-full-p.json', 'w') as file:
        json.dump(all_papers, file, indent=2)

    print(f'Scraped {len(all_papers)} papers and saved to badcase-full-p.json')

if __name__ == '__main__':
    asyncio.run(main())