import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_url(url, max_depth=1, current_depth=0, visited=None, max_pages=10):
    """
    Recursively scrapes a URL up to max_depth or max_pages.
    """
    if visited is None:
        visited = set()

    # Stop if we hit depth limit, already visited, or hit the page limit
    if current_depth > max_depth or url in visited or len(visited) >= max_pages:
        return []

    visited.add(url)
    scraped_data = []

    try:
        # Fake User-Agent to bypass basic bot-protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove javascript and stylesheet tags
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get clean text
        text = soup.get_text(separator=' ', strip=True)

        if text:
            scraped_data.append({"url": url, "content": text})
            # Added a counter to the print statement so you can track progress!
            print(f"Scraped ({len(visited)}/{max_pages}): {url}")

        # The Recursive Step
        if current_depth < max_depth:
            domain = urlparse(url).netloc
            ignore_exts = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp4', '.zip')
            
            for link in soup.find_all('a', href=True):
                # STOP looking for new links if we hit our maximum page limit
                if len(visited) >= max_pages:
                    break
                    
                next_url = urljoin(url, link['href'])
                
                if urlparse(next_url).netloc == domain and not next_url.lower().endswith(ignore_exts):
                    scraped_data.extend(
                        scrape_url(next_url, max_depth, current_depth + 1, visited, max_pages)
                    )

    except requests.RequestException as e:
        print(f"Failed to scrape {url}: {e}")

    return scraped_data