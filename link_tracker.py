"""
Module to track which links have been sent to avoid duplicates.
"""

import json
import os
from datetime import datetime


class LinkTracker:
    def __init__(self, tracking_file='sent_links.json'):
        self.tracking_file = tracking_file
        self.data = self._load_data()

    def _load_data(self):
        """Load tracking data from file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading tracking file: {e}")
                return {'sent_links': [], 'history': []}
        return {'sent_links': [], 'history': []}

    def _save_data(self):
        """Save tracking data to file."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving tracking file: {e}")

    def is_sent(self, url):
        """Check if a URL has been sent before."""
        return url in self.data['sent_links']

    def mark_as_sent(self, url, title=None):
        """Mark a URL as sent."""
        if url not in self.data['sent_links']:
            self.data['sent_links'].append(url)

        # Add to history with timestamp
        self.data['history'].append({
            'url': url,
            'title': title,
            'date': datetime.now().isoformat()
        })

        self._save_data()

    def get_unsent_links(self, all_links):
        """
        Get links that haven't been sent yet.

        Args:
            all_links: List of all available links

        Returns:
            List of unsent links
        """
        return [link for link in all_links if not self.is_sent(link)]

    def get_history(self, limit=10):
        """Get recent history of sent links."""
        history = self.data['history']
        return history[-limit:] if len(history) > limit else history

    def reset(self):
        """Reset all tracking data."""
        self.data = {'sent_links': [], 'history': []}
        self._save_data()

    def get_stats(self):
        """Get statistics about sent links."""
        return {
            'total_sent': len(self.data['sent_links']),
            'last_sent': self.data['history'][-1] if self.data['history'] else None
        }


if __name__ == "__main__":
    # Test the tracker
    tracker = LinkTracker('test_tracking.json')

    # Test adding links
    test_links = [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3"
    ]

    print("Testing LinkTracker...")
    print(f"\nInitial stats: {tracker.get_stats()}")

    # Mark first link as sent
    tracker.mark_as_sent(test_links[0], "Test Article 1")
    print(f"\nAfter marking first link: {tracker.get_stats()}")

    # Check which links are unsent
    unsent = tracker.get_unsent_links(test_links)
    print(f"\nUnsent links: {len(unsent)}")
    for link in unsent:
        print(f"  - {link}")

    # Get history
    print(f"\nHistory: {tracker.get_history()}")

    # Clean up test file
    if os.path.exists('test_tracking.json'):
        os.remove('test_tracking.json')
    print("\nTest completed!")
