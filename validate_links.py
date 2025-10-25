#!/usr/bin/env python3
"""
Validate links in your Google Doc reading list.
This script checks which links can be scraped successfully.
"""

import sys
from google_doc_fetcher import get_links_from_google_doc
from article_scraper import scrape_article
from link_tracker import LinkTracker


def validate_links(doc_url):
    """Check which links in the doc can be scraped successfully."""
    print("Fetching links from Google Doc...")
    all_links = get_links_from_google_doc(doc_url)

    if not all_links:
        print("Error: No links found in the Google Doc")
        return

    print(f"Found {len(all_links)} total links\n")
    print("=" * 80)
    print("Validating links...")
    print("=" * 80)

    valid_links = []
    invalid_links = []

    for i, link in enumerate(all_links, 1):
        print(f"\n[{i}/{len(all_links)}] Testing: {link}")
        print("-" * 80)

        result = scrape_article(link)

        # Check if scraping was successful AND has meaningful content
        if result['success'] and len(result.get('text', '')) > 100:
            print(f"✓ SUCCESS")
            print(f"  Title: {result['title']}")
            print(f"  Content length: {len(result['text'])} characters")
            valid_links.append(link)
        else:
            print(f"✗ FAILED")
            if not result['success']:
                error = result.get('error', 'Unknown error')
            else:
                error = f"Insufficient content ({len(result.get('text', ''))} characters)"
            print(f"  Error: {error}")
            invalid_links.append({
                'url': link,
                'error': error
            })

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total links: {len(all_links)}")
    print(f"Valid links: {len(valid_links)} ✓")
    print(f"Invalid links: {len(invalid_links)} ✗")

    if invalid_links:
        print("\n⚠️  PROBLEMATIC LINKS:")
        print("-" * 80)
        for item in invalid_links:
            print(f"\n❌ {item['url']}")
            print(f"   Error: {item['error']}")

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        print("1. Remove or replace the problematic links in your Google Doc")
        print("2. For Substack articles, use the public article URL, not inbox links")
        print("   ❌ Bad:  https://substack.com/inbox/post/...")
        print("   ✓ Good: https://author.substack.com/p/article-title")
        print("3. For paywalled content, the scraper may not work")
        print("4. Some sites block scrapers - try accessing in a browser first")

    else:
        print("\n🎉 All links are valid and can be scraped!")


if __name__ == "__main__":
    # Get doc URL from environment variable or use default
    import os

    doc_url = os.getenv('GOOGLE_DOC_URL')

    if not doc_url:
        print("Error: Please set GOOGLE_DOC_URL environment variable")
        print("Example: export GOOGLE_DOC_URL='https://docs.google.com/document/d/YOUR_DOC_ID/edit'")
        sys.exit(1)

    validate_links(doc_url)
