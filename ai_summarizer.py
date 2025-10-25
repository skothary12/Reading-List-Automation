"""
Module to generate AI summaries using OpenAI API.
"""

from openai import OpenAI


def summarize_article(title, text, api_key):
    """
    Generate a summary of an article using OpenAI's API.

    Args:
        title: Article title
        text: Article text content
        api_key: OpenAI API key

    Returns:
        Dictionary with summary and metadata
    """
    try:
        client = OpenAI(api_key=api_key)

        # Truncate text if too long (GPT has token limits)
        # Roughly 4 characters per token, keep it under 12k tokens for input
        max_chars = 48000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        prompt = f"""Please provide a comprehensive summary of the following article.

Title: {title}

Article Content:
{text}

Please provide:
1. A brief 2-3 sentence overview
2. Key points and main arguments (3-5 bullet points)
3. Any important conclusions or takeaways

Keep the summary informative but concise, suitable for a daily reading digest email."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the cost-effective mini model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates clear, informative summaries of articles and reports."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        summary = response.choices[0].message.content

        return {
            'summary': summary,
            'success': True,
            'model': response.model,
            'tokens_used': response.usage.total_tokens
        }

    except Exception as e:
        print(f"Error generating summary: {e}")
        return {
            'summary': None,
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the summarizer
    import os

    # Get API key from environment variable for testing
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("Error: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key'")
        exit(1)

    test_title = "How to avoid past edtech pitfalls as we begin using AI to scale impact in education"
    test_text = """Artificial intelligence holds promise for education, but only if we learn from past technology implementation failures. This article examines how to avoid repeating mistakes made with previous educational technology initiatives."""

    result = summarize_article(test_title, test_text, api_key)

    if result['success']:
        print(f"Summary generated successfully!")
        print(f"Model: {result['model']}")
        print(f"Tokens used: {result['tokens_used']}")
        print(f"\nSummary:\n{result['summary']}")
    else:
        print(f"Failed to generate summary: {result['error']}")
