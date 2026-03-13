import os

NEWS_API_KEY        = os.environ.get('NEWS_API_KEY',        '')
EMAIL               = os.environ.get('EMAIL',               '')
PASSWORD            = os.environ.get('PASSWORD',            '')
TO_EMAILS           = [e.strip() for e in os.environ.get('TO_EMAILS', '').split(',') if e.strip()]
ANTHROPIC_API_KEY   = os.environ.get('ANTHROPIC_API_KEY',   '')
MAILCHIMP_API_KEY   = os.environ.get('MAILCHIMP_API_KEY',   '')
MAILCHIMP_LIST_ID   = os.environ.get('MAILCHIMP_LIST_ID',   '')
MAILCHIMP_DC        = os.environ.get('MAILCHIMP_DC',        '')
