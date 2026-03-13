import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from config import EMAIL, PASSWORD, TO_EMAILS

def send_email(message, html):
    """Wysyła email z newsami do wszystkich odbiorców."""
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL, PASSWORD)
            for to_email in TO_EMAILS:
                msg = MIMEText(html, 'html')  # Tworzymy nowy obiekt msg dla każdego odbiorcy
                msg['Subject'] = f'Daily coffee news ({datetime.now().strftime("%Y-%m-%d")})'
                msg['From'] = EMAIL
                msg['To'] = to_email
                server.send_message(msg)
                print(f"Email wysłany do {to_email} o {datetime.now()}")
    except Exception as e:
        print(f"Błąd email: {str(e)}")