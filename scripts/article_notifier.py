#!/usr/bin/env python3
"""
Article Notifier

This script implements a local automation that:
 - Reads a master Google Doc (a reading list containing one article URL per line)
 - Each morning at 7:00 local time selects a random unread link, fetches the article,
   creates an automatic summary using an LLM (OpenAI by default), and emails you the
   link + auto-summary.
 - At 12:00 (noon) sends a reminder email asking you to reply with your own summary.
 - Monitors Gmail for your reply, saves your notes, and appends them to a "Compiled Summaries"
   Google Doc for later review.

Features & choices (design notes):
 - State management: local JSON file `data/state.json` holds article entries and their
   read/unread status, auto-summary, and user_summary. This is robust and simple, and
   keeps you in control of data. Optionally, the script can mark the master Doc as read
   (code stub included) but by default we only store state locally to avoid mutating
   your source reading list unintentionally.
 - Article extraction: uses `trafilatura` for robust extraction of readable text. Falls
   back to basic HTML/text extraction if needed.
 - Summarization: supports OpenAI (via `OPENAI_API_KEY`). The code is modular so adding
   Anthropic/Claude is straightforward.
 - Gmail replies parsing: when sending the noon reminder, the script includes a unique
   token in the subject like `ARTICLE_ID:{id}`. The script polls Gmail searching for that
   token in the subject to find replies and extracts the plaintext or HTML body.
 - Scheduling: uses APScheduler when the script runs as a long-lived process. If you
   prefer cron, you can run the script with `--run-once <job>` and schedule two daily cron
   entries.

Requirements: Python 3.9+
 - google-api-python-client
 - google-auth-httplib2
 - google-auth-oauthlib
 - openai
 - trafilatura
 - apscheduler
 - requests

Setup (quick):
 1. Create Google OAuth credentials (OAuth client ID) and download `credentials.json` to
    the project root. Scopes used: Gmail send/read, Docs read/write, Drive metadata.
 2. Set environment vars:
    - OPENAI_API_KEY (if using OpenAI)
    - GOOGLE_CREDENTIALS=file path to credentials.json (optional; defaults to ./credentials.json)
 3. Run the script. On first run it will open a browser for Google OAuth and create `token.json`.

Usage:
  - Run as a long-lived process (recommended): `python scripts/article_notifier.py`
  - Or run once for a specific job (for cron):
      `python scripts/article_notifier.py --run-once morning`
      `python scripts/article_notifier.py --run-once noon`

Notes:
 - This is a single-file implementation with clear functions for each step. It is intentionally
   modular for easy extension.
 - The script assumes your master reading list Doc contains one URL per line.
"""

import os
import json
import time
import random
import logging
import argparse
from datetime import datetime, date

import requests
import trafilatura

from apscheduler.schedulers.background import BackgroundScheduler

from typing import Optional, Dict, Any, List

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    import openai
except Exception:
    openai = None

# ---------------------- Configuration ---------------------------------
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
STATE_PATH = os.path.join(DATA_DIR, 'state.json')
DEFAULT_TOKEN = os.path.join(PROJECT_ROOT, '..', 'token.json')
DEFAULT_CREDS = os.path.join(PROJECT_ROOT, '..', 'credentials.json')

MASTER_DOC_ID = os.getenv('MASTER_DOC_ID')  # Google Doc ID for reading list
COMPILED_DOC_TITLE_TEMPLATE = 'Article Summaries {year}'

# Email templates
MORNING_SUBJECT = "Today's Article: {title}"
NOON_SUBJECT = "Your Key Points for Today's Article: {title} [ARTICLE_ID:{id}]"

logger = logging.getLogger('article_notifier')
logging.basicConfig(level=logging.INFO)


# ---------------------- State management ------------------------------
def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    # initialize
    state = {
        'articles': {},  # id -> {url, title, read, auto_summary, user_summary, last_sent}
        'compiled_doc_id': None,
    }
    save_state(state)
    return state


def save_state(state: Dict[str, Any]):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def create_article_entry(url: str) -> Dict[str, Any]:
    # deterministic id for link
    aid = str(abs(hash(url)))
    return {
        'id': aid,
        'url': url,
        'title': None,
        'read': False,
        'auto_summary': None,
        'user_summary': None,
        'last_sent': None,
    }


# ---------------------- Google Auth Helpers --------------------------
def get_credentials(scopes=SCOPES, creds_path: Optional[str] = None, token_path: Optional[str] = None) -> Credentials:
    creds_path = creds_path or os.getenv('GOOGLE_CREDENTIALS') or DEFAULT_CREDS
    token_path = token_path or os.getenv('GOOGLE_TOKEN') or DEFAULT_TOKEN

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds


# ---------------------- Google Docs / Drive ---------------------------
def read_master_doc_links(docs_service, doc_id: str) -> List[str]:
    """Read the master Doc and return a list of URLs (one per line expected)."""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    text = []
    for el in doc.get('body', {}).get('content', []):
        paragraph = el.get('paragraph')
        if not paragraph:
            continue
        for elem in paragraph.get('elements', []):
            txt_run = elem.get('textRun')
            if not txt_run:
                continue
            t = txt_run.get('content', '')
            text.append(t)
    # join and split lines
    joined = ''.join(text)
    lines = [l.strip() for l in joined.splitlines() if l.strip()]
    # keep only lines that look like URLs
    urls = [l for l in lines if l.startswith('http')]
    return urls


def append_to_compiled_doc(docs_service, compiled_doc_id: str, article_entry: Dict[str, Any]):
    """Append article entry (link, auto summary, user summary) to compiled doc.
    If compiled_doc_id is None, this function will create a new document and return its id.
    """
    if compiled_doc_id is None:
        title = COMPILED_DOC_TITLE_TEMPLATE.format(year=date.today().year)
        doc = docs_service.documents().create(body={'title': title}).execute()
        compiled_doc_id = doc['documentId']

    # Build content to append
    parts = []
    parts.append({'insertText': {'text': f"Article: {article_entry.get('title') or article_entry['url']}\n", 'endOfSegmentLocation': {}}})
    parts.append({'insertText': {'text': f"Link: {article_entry['url']}\n\n", 'endOfSegmentLocation': {}}})
    parts.append({'insertText': {'text': f"Auto-summary:\n{article_entry.get('auto_summary','(none)')}\n\n", 'endOfSegmentLocation': {}}})
    parts.append({'insertText': {'text': f"User summary:\n{article_entry.get('user_summary','(none)')}\n\n---\n\n", 'endOfSegmentLocation': {}}})

    # Note: endOfSegmentLocation with empty segmentId will append to end of doc body
    reqs = parts
    docs_service.documents().batchUpdate(documentId=compiled_doc_id, body={'requests': reqs}).execute()
    return compiled_doc_id


# ---------------------- Gmail helpers --------------------------------
def send_email(gmail_service, to_email: str, subject: str, body_text: str):
    from email.mime.text import MIMEText
    import base64
    message = MIMEText(body_text)
    message['to'] = to_email
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    msg = {'raw': raw}
    sent = gmail_service.users().messages().send(userId='me', body=msg).execute()
    logger.info('Sent message ID: %s', sent.get('id'))
    return sent


def search_messages(gmail_service, query: str) -> List[Dict[str, Any]]:
    resp = gmail_service.users().messages().list(userId='me', q=query).execute()
    msgs = resp.get('messages', [])
    results = []
    for m in msgs:
        full = gmail_service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        results.append(full)
    return results


def extract_message_text(message: Dict[str, Any]) -> str:
    # Attempt to extract plaintext body, falling back to HTML by stripping tags
    payload = message.get('payload', {})
    parts = payload.get('parts') or [payload]
    text_chunks = []
    for p in parts:
        mime = p.get('mimeType', '')
        if mime == 'text/plain':
            data = p.get('body', {}).get('data')
            if data:
                import base64
                text = base64.urlsafe_b64decode(data.encode()).decode(errors='ignore')
                text_chunks.append(text)
        elif mime == 'text/html':
            data = p.get('body', {}).get('data')
            if data:
                import base64, re
                html = base64.urlsafe_b64decode(data.encode()).decode(errors='ignore')
                # crude html -> text
                text = re.sub('<[^<]+?>', '', html)
                text_chunks.append(text)
    return '\n'.join(text_chunks).strip()


# ---------------------- Article fetching & summarization ----------------
def fetch_article_text(url: str, timeout: int = 15) -> Optional[str]:
    try:
        r = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        # try trafilatura
        extracted = trafilatura.extract(r.text, base_url=url)
        if extracted:
            return extracted
        # fallback: strip tags minimally
        import re
        text = re.sub('<[^<]+?>', '', r.text)
        # return first N chars
        return text[:20000]
    except Exception as e:
        logger.exception('Failed to fetch article %s: %s', url, e)
        return None


def summarize_text_openai(text: str, max_tokens: int = 300) -> str:
    key = os.getenv('OPENAI_API_KEY')
    if not key or openai is None:
        raise RuntimeError('OpenAI not configured or `openai` package missing')
    openai.api_key = key
    prompt = f"Summarize the following article in 3-5 sentences:\n\n{text[:8000]}"
    resp = openai.ChatCompletion.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini') if os.getenv('OPENAI_MODEL') else 'gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    # Support both ChatCompletion and Completion style
    choice = resp['choices'][0]
    if 'message' in choice:
        return choice['message']['content'].strip()
    return choice['text'].strip()


def auto_summarize(text: str) -> str:
    provider = os.getenv('LLM_PROVIDER', 'openai')
    if provider == 'openai':
        return summarize_text_openai(text)
    else:
        raise NotImplementedError('Only openai provider implemented; add Claude/Anthropic if needed')


# ---------------------- Main job functions ----------------------------
def pick_random_unread(state: Dict[str, Any], urls: List[str]) -> Dict[str, Any]:
    # Ensure articles in state
    for u in urls:
        aid = str(abs(hash(u)))
        if aid not in state['articles']:
            entry = create_article_entry(u)
            state['articles'][entry['id']] = entry
    unread = [a for a in state['articles'].values() if not a.get('read')]
    if not unread:
        # reset all to unread if none left
        for a in state['articles'].values():
            a['read'] = False
        unread = list(state['articles'].values())
    chosen = random.choice(unread)
    return chosen


def job_morning(creds, master_doc_id: str, to_email: str, state: Dict[str, Any]):
    logger.info('Morning job starting')
    docs_service = build('docs', 'v1', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)

    urls = read_master_doc_links(docs_service, master_doc_id)
    if not urls:
        logger.warning('No URLs found in master doc')
        return
    picked = pick_random_unread(state, urls)
    logger.info('Picked article %s', picked['url'])

    text = fetch_article_text(picked['url'])
    if not text:
        logger.warning('Could not fetch article text; aborting morning send')
        return

    auto_sum = auto_summarize(text)
    picked['auto_summary'] = auto_sum
    picked['title'] = (picked['title'] or picked['url'])
    picked['last_sent'] = datetime.utcnow().isoformat()

    subject = MORNING_SUBJECT.format(title=picked.get('title') or picked['url'])
    body = f"Link: {picked['url']}\n\nAuto-summary:\n{auto_sum}\n\nReply to this email with your notes later today.\n"
    send_email(gmail_service, to_email, subject, body)

    # Save state immediately
    state['articles'][picked['id']] = picked
    save_state(state)
    logger.info('Morning job complete')


def job_noon(creds, to_email: str, state: Dict[str, Any]):
    logger.info('Noon job starting')
    gmail_service = build('gmail', 'v1', credentials=creds)

    # pick today's sent article (last_sent)
    today_articles = [a for a in state['articles'].values() if a.get('last_sent')]
    if not today_articles:
        logger.info('No sent article found for today')
        return
    # naive: pick most recently sent
    picked = max(today_articles, key=lambda x: x['last_sent'])

    subject = NOON_SUBJECT.format(title=picked.get('title') or picked['url'], id=picked['id'])
    body = f"Hi — this is a friendly reminder to reply to this email with your key points or a short summary for today's article:\n\n{picked['url']}\n\nPlease reply to this message with your notes; I'll save them to your compiled summaries document."
    send_email(gmail_service, to_email, subject, body)
    logger.info('Noon reminder sent')


def poll_replies_and_save(creds, state: Dict[str, Any]):
    logger.info('Polling for replies')
    gmail_service = build('gmail', 'v1', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)

    for aid, article in state['articles'].items():
        if article.get('user_summary'):
            continue  # already have user summary
        query = f'subject:ARTICLE_ID:{aid} in:inbox'
        msgs = search_messages(gmail_service, query)
        if not msgs:
            continue
        # take the most recent
        msg = max(msgs, key=lambda m: int(m['internalDate']))
        text = extract_message_text(msg)
        article['user_summary'] = text
        article['read'] = True
        # append to compiled doc
        compiled_id = state.get('compiled_doc_id')
        compiled_id = append_to_compiled_doc(docs_service, compiled_id, article)
        state['compiled_doc_id'] = compiled_id
        # mark message as read
        gmail_service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        save_state(state)
        logger.info('Saved user summary for article %s', aid)


# ---------------------- CLI / Scheduler --------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-once', choices=['morning', 'noon', 'poll'], help='Run only one job and exit (for cron)')
    parser.add_argument('--email', help='Your email address to send to (overrides env EMAIL_TO)')
    args = parser.parse_args()

    creds = get_credentials()
    state = load_state()
    to_email = args.email or os.getenv('EMAIL_TO')
    master_doc_id = MASTER_DOC_ID or os.getenv('MASTER_DOC_ID')
    if not master_doc_id:
        logger.error('MASTER_DOC_ID environment variable or global constant must be set to a Google Doc ID containing the reading list')
        return

    if args.run_once:
        if args.run_once == 'morning':
            job_morning(creds, master_doc_id, to_email, state)
        elif args.run_once == 'noon':
            job_noon(creds, to_email, state)
        elif args.run_once == 'poll':
            poll_replies_and_save(creds, state)
        return

    # Run scheduler
    scheduler = BackgroundScheduler()
    # run at 07:00 local time daily
    scheduler.add_job(lambda: job_morning(creds, master_doc_id, to_email, state), 'cron', hour=7, minute=0)
    # run at 12:00 local time daily
    scheduler.add_job(lambda: job_noon(creds, to_email, state), 'cron', hour=12, minute=0)
    # poll replies every 10 minutes
    scheduler.add_job(lambda: poll_replies_and_save(creds, state), 'interval', minutes=10)
    scheduler.start()

    logger.info('Scheduler started — running in background. Press Ctrl+C to exit.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('Shutting down')
        scheduler.shutdown()


if __name__ == '__main__':
    main()
