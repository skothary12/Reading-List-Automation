#!/usr/bin/env python3
"""
Simple test script to download Google Doc contents.
Note: Google Docs API doesn't support API keys for document access.
This script uses the public export URL instead for publicly shared documents.
"""

import requests

# Configuration
DOC_URL = "https://docs.google.com/document/d/1E0GgKbBtw3zhM3x8_qXykgXFndiMMGh3t_249hhcPVs/edit?usp=sharing"

# Extract document ID from URL
def extract_doc_id(url):
    """Extract the document ID from a Google Docs URL."""
    # Format: https://docs.google.com/document/d/{DOC_ID}/edit
    parts = url.split('/d/')
    if len(parts) > 1:
        doc_id = parts[1].split('/')[0]
        return doc_id
    return None

def download_google_doc_as_text(doc_id):
    """Download a publicly shared Google Doc as plain text."""
    # Google Docs export URL for plain text
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    print(f"Fetching document ID: {doc_id}")
    print(f"Export URL: {export_url}\n")

    try:
        response = requests.get(export_url)
        response.raise_for_status()

        content = response.text

        # Print document content
        print("=" * 60)
        print("DOCUMENT CONTENT (Plain Text)")
        print("=" * 60)
        print(content)
        print()

        # Save to file
        output_file = "downloaded_doc.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Content saved to: {output_file}")

        return content

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 404:
            print("The document may not be publicly accessible or the ID is incorrect.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def download_google_doc_as_html(doc_id):
    """Download a publicly shared Google Doc as HTML."""
    # Google Docs export URL for HTML
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"

    print(f"\nFetching HTML version...")
    print(f"Export URL: {export_url}\n")

    try:
        response = requests.get(export_url)
        response.raise_for_status()

        content = response.text

        # Save to file
        output_file = "downloaded_doc.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"HTML content saved to: {output_file}")

        return content

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error downloading HTML: {e}")
        return None
    except Exception as e:
        print(f"Error downloading HTML: {e}")
        return None

if __name__ == "__main__":
    print("Google Docs Download Test Script")
    print("=" * 60)
    print()

    # Extract document ID from URL
    doc_id = extract_doc_id(DOC_URL)

    if not doc_id:
        print("Error: Could not extract document ID from URL")
        exit(1)

    # Download the document as plain text
    result_text = download_google_doc_as_text(doc_id)

    # Also download as HTML for better formatting preservation
    result_html = download_google_doc_as_html(doc_id)

    if result_text:
        print("\n✓ Success! Document downloaded successfully.")
        print("\nAvailable export formats:")
        print("  - Plain text: downloaded_doc.txt")
        if result_html:
            print("  - HTML: downloaded_doc.html")
    else:
        print("\n✗ Failed to download document.")
        print("\nTroubleshooting:")
        print("1. Make sure the document is shared with 'Anyone with the link can view'")
        print("2. Check that the document URL is correct")
        print("3. Verify the document exists and is accessible")
