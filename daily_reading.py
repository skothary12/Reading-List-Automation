#!/usr/bin/env python3
"""
Daily Reading Automation Script

This script:
1. Fetches links from your Google Doc
2. Selects a random link that hasn't been sent yet
3. Scrapes the article content
4. Generates an AI summary
5. Emails the summary to you

Run this script daily (e.g., via cron job) to get your daily reading digest.
"""

import json
import random
import sys
import os
from datetime import datetime

from google_doc_fetcher import get_links_from_google_doc
from article_scraper import scrape_article
from ai_summarizer import summarize_article
from email_sender import send_email
from link_tracker import LinkTracker


def load_config(config_file='config.json'):
    """Load configuration from JSON file or environment variables."""
    # Try to load from environment variables first (for GitHub Actions)
    if os.getenv('GOOGLE_DOC_URL'):
        print("Loading configuration from environment variables...")
        return {
            'google_doc_url': os.getenv('GOOGLE_DOC_URL'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'email': {
                'to': os.getenv('EMAIL_TO'),
                'smtp': {
                    'server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                    'port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
                    'email': os.getenv('EMAIL_ADDRESS'),
                    'password': os.getenv('EMAIL_PASSWORD')
                }
            },
            'tracking_file': 'sent_links.json'
        }

    # Otherwise, load from config.json (for local usage)
    try:
        print("Loading configuration from config.json...")
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)


def main():
    """Main function to orchestrate the daily reading workflow."""
    print("=" * 60)
    print("Daily Reading Automation")
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print("=" * 60)
    print()

    # Load configuration
    print("Loading configuration...")
    config = load_config()

    # Initialize link tracker
    tracker = LinkTracker(config.get('tracking_file', 'sent_links.json'))

    # Get links from Google Doc
    print("Fetching links from Google Doc...")
    all_links = get_links_from_google_doc(config['google_doc_url'])

    if not all_links:
        print("Error: No links found in the Google Doc")
        sys.exit(1)

    print(f"Found {len(all_links)} total links")

    # Filter out already sent links
    unsent_links = tracker.get_unsent_links(all_links)

    if not unsent_links:
        print("\nAll links have been sent!")
        print("Resetting tracker to start over...")
        tracker.reset()
        unsent_links = all_links

    print(f"Available unsent links: {len(unsent_links)}")

    # Try multiple articles if scraping fails
    max_attempts = min(3, len(unsent_links))
    article = None
    selected_link = None

    for attempt in range(max_attempts):
        # Select a random link
        selected_link = random.choice(unsent_links)
        print(f"\nAttempt {attempt + 1}/{max_attempts}")
        print(f"Selected article: {selected_link}")

        # Scrape the article
        print("Scraping article content...")
        article = scrape_article(selected_link)

        # Check if scraping was successful AND has meaningful content
        if article['success'] and len(article.get('text', '')) > 100:
            print(f"✓ Successfully scraped article")
            break
        else:
            # Determine the error message
            if not article['success']:
                error_msg = article.get('error', 'Unknown error')
            else:
                error_msg = f"Article has insufficient content ({len(article.get('text', ''))} characters)"

            print(f"✗ Error: {error_msg}")
            print(f"Marking this link as failed and trying another...")
            # Mark as sent so we don't retry it
            tracker.mark_as_sent(selected_link, f"FAILED: {error_msg[:100]}")
            # Remove from unsent list for this run
            unsent_links.remove(selected_link)
            if not unsent_links:
                print("\nNo more unsent links available")
                sys.exit(1)
            article = None

    if not article or not article['success']:
        print(f"\nFailed to scrape any articles after {max_attempts} attempts")
        sys.exit(1)

    print(f"Title: {article['title']}")
    print(f"Content length: {len(article['text'])} characters")

    # Generate AI summary (with fallback if it fails)
    print("\nGenerating AI summary...")
    summary_result = summarize_article(
        article['title'],
        article['text'],
        config['openai_api_key']
    )

    summary_text = None
    if not summary_result['success']:
        print(f"⚠️  Warning: Failed to generate AI summary: {summary_result.get('error', 'Unknown error')}")
        print("Continuing with fallback summary...")

        # Create a fallback summary with article preview
        preview_length = 500
        preview_text = article['text'][:preview_length].strip()
        if len(article['text']) > preview_length:
            preview_text += "..."

        summary_text = f"""⚠️ AI Summary Unavailable

The AI summarization service is currently unavailable. Here's a preview of the article:

{preview_text}

Please read the full article using the link below."""
    else:
        print(f"✓ Summary generated successfully ({summary_result['tokens_used']} tokens used)")
        summary_text = summary_result['summary']

    # Send email
    print("\nSending email...")
    email_subject = f"📚 Daily Reading: {article['title']}"

    email_result = send_email(
        to_email=config['email']['to'],
        subject=email_subject,
        title=article['title'],
        url=selected_link,
        summary=summary_text,
        smtp_config=config['email']['smtp']
    )

    if not email_result['success']:
        print(f"Error sending email: {email_result.get('error', 'Unknown error')}")
        sys.exit(1)

    print(email_result['message'])

    # Mark link as sent
    tracker.mark_as_sent(selected_link, article['title'])

    # Print stats
    stats = tracker.get_stats()
    print("\n" + "=" * 60)
    print("Success!")
    print(f"Total articles sent so far: {stats['total_sent']}")
    print(f"Remaining unsent articles: {len(unsent_links) - 1}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
