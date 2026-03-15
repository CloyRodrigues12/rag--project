import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures

def process_single_page(url, domain, ignore_exts):
    """Worker function that grabs a single page and extracts its links."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Find new links to feed back to the thread pool
        new_links = []
        for link in soup.find_all('a', href=True):
            next_url = urljoin(url, link['href'])
            if urlparse(next_url).netloc == domain and not next_url.lower().endswith(ignore_exts):
                new_links.append(next_url)
                
        return url, text, new_links
        
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return url, None, []

def scrape_url(start_url, max_pages=50): # Increased to 50 pages!
    """Manages the thread pool and coordinates the parallel scraping."""
    print(f"\n🚀 Initiating Multithreaded Scraper (Max Pages: {max_pages})")
    
    visited = set([start_url])
    to_visit = [start_url]
    scraped_data = []
    
    domain = urlparse(start_url).netloc
    ignore_exts = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.zip')

    # Spawn 10 parallel worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while to_visit and len(scraped_data) < max_pages:
            
            # Dispatch the current batch of URLs to the worker threads
            future_to_url = {executor.submit(process_single_page, url, domain, ignore_exts): url for url in to_visit}
            to_visit = [] # Clear the queue for the next wave
            
            # As each thread finishes its page, process the results
            for future in concurrent.futures.as_completed(future_to_url):
                if len(scraped_data) >= max_pages:
                    break
                    
                url, text, links = future.result()
                
                if text:
                    scraped_data.append({"url": url, "content": text})
                    print(f"Scraped ({len(scraped_data)}/{max_pages}): {url}")
                    
                # Add newly discovered links to the queue if we haven't seen them
                for link in links:
                    if link not in visited and len(visited) < max_pages * 2: # buffer to prevent infinite queue buildup
                        visited.add(link)
                        to_visit.append(link)

    return scraped_data