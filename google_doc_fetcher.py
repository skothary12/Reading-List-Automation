"""
Module to fetch and parse links from a Google Doc.
"""

import requests
import re


def extract_doc_id(url):
    """Extract the document ID from a Google Docs URL."""
    parts = url.split('/d/')
    if len(parts) > 1:
        doc_id = parts[1].split('/')[0]
        return doc_id
    return None


def fetch_google_doc(doc_id):
    """Download a publicly shared Google Doc as plain text."""
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    try:
        response = requests.get(export_url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching Google Doc: {e}")
        return None


def extract_links(text):
    """Extract all URLs from text content."""
    # Pattern to match URLs (http, https)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)

    # Clean up URLs (remove trailing punctuation, etc.)
    cleaned_urls = []
    for url in urls:
        # Remove trailing punctuation
        url = url.rstrip('.,;:!?)')
        cleaned_urls.append(url)

    return list(set(cleaned_urls))  # Remove duplicates


def get_links_from_google_doc(doc_url):
    """
    Main function to get all links from a Google Doc.

    Args:
        doc_url: The Google Doc URL

    Returns:
        List of URLs found in the document
    """
    doc_id = extract_doc_id(doc_url)
    if not doc_id:
        print("Error: Could not extract document ID from URL")
        return []

    content = fetch_google_doc(doc_id)
    if not content:
        return []

    links = extract_links(content)
    return links


if __name__ == "__main__":
    # Test the module
    DOC_URL = "https://docs.google.com/document/d/1E0GgKbBtw3zhM3x8_qXykgXFndiMMGh3t_249hhcPVs/edit?usp=sharing"

    links = get_links_from_google_doc(DOC_URL)
    print(f"Found {len(links)} links:")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link}")
