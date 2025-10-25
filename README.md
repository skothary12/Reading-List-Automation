# Daily Reading List Automation

Automatically receive a daily email with a randomly selected article from your Google Doc reading list, complete with an AI-generated summary.

## Overview

This system:
1. Fetches links from your Google Doc
2. Selects a random link that hasn't been sent yet
3. Scrapes the article content
4. Generates an AI summary using OpenAI
5. Emails the summary to you
6. Tracks which articles have been sent to avoid duplicates

## Files

- `daily_reading.py` — Main script that orchestrates the daily workflow
- `google_doc_fetcher.py` — Fetches and parses links from Google Doc
- `article_scraper.py` — Scrapes article content from URLs
- `ai_summarizer.py` — Generates summaries using OpenAI API
- `email_sender.py` — Sends formatted HTML emails
- `link_tracker.py` — Tracks which links have been sent
- `config.json` — Configuration file (see setup below)
- `requirements.txt` — Python dependencies

## Setup

### Option 1: GitHub Actions (Recommended)

This is the easiest way to run the script daily without keeping your computer on.

#### 1. Fork or Push to GitHub

Push this repository to your GitHub account.

#### 2. Set up Gmail App Password

1. Enable 2-factor authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Save this password - you'll need it for the next step

#### 3. Configure GitHub Secrets

Go to your repository on GitHub → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `GOOGLE_DOC_URL` | Your Google Doc URL | `https://docs.google.com/document/d/...` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `EMAIL_TO` | Your email address (recipient) | `your-email@gmail.com` |
| `EMAIL_SMTP_SERVER` | SMTP server | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `EMAIL_ADDRESS` | Your email address (sender) | `your-email@gmail.com` |
| `EMAIL_PASSWORD` | Gmail app password from step 2 | `abcd efgh ijkl mnop` |

#### 4. Enable GitHub Actions

1. Go to the "Actions" tab in your repository
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. The workflow will run automatically every day at 8:00 AM UTC

#### 5. Adjust Schedule (Optional)

To change when emails are sent, edit `.github/workflows/daily_reading.yml`:

```yaml
schedule:
  # Examples:
  - cron: '0 8 * * *'   # 8:00 AM UTC daily
  - cron: '0 13 * * *'  # 1:00 PM UTC (8:00 AM EST) daily
  - cron: '0 15 * * *'  # 3:00 PM UTC (8:00 AM PST) daily
```

Use [crontab.guru](https://crontab.guru/) to help create your schedule.

#### 6. Test the Workflow

You can manually trigger the workflow:
1. Go to Actions tab
2. Select "Daily Reading Digest"
3. Click "Run workflow"
4. Click the green "Run workflow" button

### Option 2: Run Locally

#### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

#### 2. Configure Your Settings

Edit `config.json` with your information:

```json
{
  "google_doc_url": "YOUR_GOOGLE_DOC_URL",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "email": {
    "to": "your-email@example.com",
    "smtp": {
      "server": "smtp.gmail.com",
      "port": 587,
      "email": "your-email@gmail.com",
      "password": "your-app-password"
    }
  },
  "tracking_file": "sent_links.json"
}
```

#### 3. Run Manually

```bash
python3 daily_reading.py
```

#### 4. Schedule with Cron (macOS/Linux)

```bash
crontab -e
```

Add:
```bash
0 8 * * * cd /path/to/Reading-List-Automation && /usr/bin/python3 daily_reading.py
```

## Google Doc Setup

Your Google Doc should:
- Be shared with "Anyone with the link can view"
- Contain URLs to articles (one per line or in bullet points)

## How It Works

1. The script reads your Google Doc and extracts all URLs
2. It checks which links haven't been sent yet (tracked in `sent_links.json`)
3. Randomly selects one unsent link
4. Scrapes the article content using BeautifulSoup
5. Sends the content to OpenAI to generate a summary
6. Emails you a beautifully formatted HTML email with the summary
7. Marks the link as sent so it won't be repeated

When all links have been sent, it automatically resets and starts over.

## Troubleshooting

**Email not sending:**
- Verify your SMTP credentials
- For Gmail, ensure you're using an App Password, not your regular password
- Check that 2FA is enabled on your Google account

**No links found in Google Doc:**
- Ensure the document is shared publicly ("Anyone with the link can view")
- Verify the document URL is correct
- Check that URLs are properly formatted in the document

**Article scraping fails:**
- Some websites block scrapers - this is normal
- The script will show an error and exit if scraping fails
- You can manually mark that link as sent by editing `sent_links.json`

**OpenAI API errors:**
- Verify your API key is valid
- Check your OpenAI account has credits
- The script uses `gpt-4o-mini` which is cost-effective

## Cost Estimates

- OpenAI API: ~$0.01-0.03 per article (using gpt-4o-mini)
- Email: Free with Gmail
- Total monthly cost (30 articles): ~$0.30-0.90

## Security Notes

- Never commit `config.json` to a public repository (API keys and passwords!)
- Use app-specific passwords for email
- The OpenAI API key is sensitive - keep it private
- `sent_links.json` tracks your reading history locally

## Customization

You can customize:
- Email template in `email_sender.py`
- Summary prompt in `ai_summarizer.py`
- Article selection logic in `daily_reading.py` (currently random)
- Scraping selectors in `article_scraper.py`
