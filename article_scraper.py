"""
Module to scrape article content from URLs.
Uses newspaper3k for article extraction.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def scrape_article(url):
    """
    Scrape article content from a URL.

    Args:
        url: The URL to scrape

    Returns:
        Dictionary with title, text, and url
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to extract title
        title = None
        if soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        elif soup.find('title'):
            title = soup.find('title').get_text().strip()
        else:
            title = urlparse(url).netloc

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Try to find main content area
        content_areas = []

        # Common article content selectors
        selectors = [
            'article',
            '[class*="article"]',
            '[class*="content"]',
            '[class*="post"]',
            'main',
            '[role="main"]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                content_areas.extend(elements)

        # If we found content areas, use those
        if content_areas:
            text_parts = []
            for area in content_areas:
                paragraphs = area.find_all(['p', 'h2', 'h3', 'li'])
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 20:  # Filter out very short paragraphs
                        text_parts.append(text)
            text = '\n\n'.join(text_parts)
        else:
            # Fallback: just get all paragraphs
            paragraphs = soup.find_all('p')
            text_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
            text = '\n\n'.join(text_parts)

        return {
            'title': title,
            'text': text,
            'url': url,
            'success': True
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {
            'title': None,
            'text': None,
            'url': url,
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the scraper
    test_url = "https://www.brookings.edu/articles/how-to-avoid-past-edtech-pitfalls-as-we-begin-using-ai-to-scale-impact-in-education/"

    result = scrape_article(test_url)

    if result['success']:
        print(f"Title: {result['title']}")
        print(f"\nContent length: {len(result['text'])} characters")
        print(f"\nFirst 500 characters:")
        print(result['text'][:500])
    else:
        print(f"Failed to scrape: {result['error']}")
