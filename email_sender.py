import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime
from config import EMAIL, PASSWORD, TO_EMAILS, MAILCHIMP_API_KEY, MAILCHIMP_LIST_ID, MAILCHIMP_DC

def get_subscribers():
    """Fetch all subscribed emails from Mailchimp. Falls back to TO_EMAILS if not configured."""
    if not MAILCHIMP_API_KEY or not MAILCHIMP_LIST_ID or not MAILCHIMP_DC:
        return TO_EMAILS

    emails = []
    offset = 0
    while True:
        try:
            r = requests.get(
                f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/lists/{MAILCHIMP_LIST_ID}/members',
                auth=('anystring', MAILCHIMP_API_KEY),
                params={'status': 'subscribed', 'count': 1000, 'offset': offset, 'fields': 'members.email_address,total_items'},
                timeout=15,
            )
            data = r.json()
            batch = [m['email_address'] for m in data.get('members', [])]
            emails.extend(batch)
            if len(emails) >= data.get('total_items', 0) or not batch:
                break
            offset += len(batch)
        except Exception as e:
            print(f"Mailchimp fetch error: {e}")
            break

    print(f"  Subscribers: {len(emails)}")
    return emails or TO_EMAILS

def send_email(message, html, recipients=None):
    recipients = recipients or get_subscribers()
    if not recipients:
        print("No recipients found.")
        return

    date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL, PASSWORD)
            for to_email in recipients:
                msg = MIMEText(html, 'html')
                msg['Subject'] = f'The Coffee Post — {date_str}'
                msg['From']    = f'The Coffee Post <{EMAIL}>'
                msg['To']      = to_email
                server.send_message(msg)
                print(f"  Sent → {to_email}")
    except Exception as e:
        print(f"Email error: {e}")
