"""
Module to send emails with article summaries.
Supports Gmail SMTP and other email providers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def create_email_html(title, url, summary):
    """
    Create HTML formatted email content.

    Args:
        title: Article title
        url: Article URL
        summary: AI-generated summary

    Returns:
        HTML string
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #4A90E2;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .date {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .summary {{
                white-space: pre-wrap;
                margin: 15px 0;
            }}
            .link-button {{
                display: inline-block;
                background-color: #4A90E2;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #888;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">📚 Your Daily Reading</div>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
        </div>

        <div class="content">
            <h2>{title}</h2>

            <div class="summary">
{summary}
            </div>

            <p>
                <a href="{url}" class="link-button">Read Full Article</a>
            </p>
        </div>

        <div class="footer">
            <p>This is your automated daily reading digest.</p>
            <p>Article automatically selected from your reading list.</p>
        </div>
    </body>
    </html>
    """
    return html


def send_email(to_email, subject, title, url, summary, smtp_config):
    """
    Send an email with the article summary.

    Args:
        to_email: Recipient email address
        subject: Email subject
        title: Article title
        url: Article URL
        summary: AI-generated summary
        smtp_config: Dictionary with SMTP configuration
            - server: SMTP server address
            - port: SMTP port
            - email: Sender email address
            - password: Email password or app password

    Returns:
        Dictionary with success status
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject

        # Create plain text version (fallback)
        plain_text = f"""
Your Daily Reading - {datetime.now().strftime('%B %d, %Y')}

{title}

{summary}

Read the full article: {url}

---
This is your automated daily reading digest.
        """

        # Create HTML version
        html_content = create_email_html(title, url, summary)

        # Attach both versions
        part1 = MIMEText(plain_text, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['email'], smtp_config['password'])
            server.send_message(msg)

        return {
            'success': True,
            'message': f"Email sent successfully to {to_email}"
        }

    except Exception as e:
        print(f"Error sending email: {e}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test email sending
    # NOTE: You'll need to configure these settings

    test_smtp_config = {
        'server': 'smtp.gmail.com',
        'port': 587,
        'email': 'your-email@gmail.com',  # Replace with your email
        'password': 'your-app-password'    # Replace with your app password
    }

    test_title = "How to avoid past edtech pitfalls"
    test_url = "https://example.com/article"
    test_summary = "This is a test summary of the article."

    print("Email sender module created.")
    print("\nTo test email sending, update the smtp_config with your credentials.")
    print("\nFor Gmail:")
    print("1. Enable 2-factor authentication")
    print("2. Generate an App Password at https://myaccount.google.com/apppasswords")
    print("3. Use the app password in the configuration")
