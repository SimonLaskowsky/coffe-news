import requests
import re
import random
import time
from bs4 import BeautifulSoup

def _classify(score):
    score = float(score)
    if score < 25:   return "Extreme Fear"
    elif score < 45: return "Fear"
    elif score < 55: return "Neutral"
    elif score < 75: return "Greed"
    else:            return "Extreme Greed"

def get_crypto_sentiment():
    try:
        data = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5).json()
        value = int(data['data'][0]['value'])
        label = data['data'][0]['value_classification']
        return {'value': value, 'label': label, 'available': True}
    except Exception:
        return {'value': None, 'label': 'N/A', 'available': False}

def get_stock_sentiment():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    for _ in range(3):
        try:
            data = requests.get('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', headers=headers, timeout=5).json()
            fg = data.get('fear_and_greed', {})
            value = fg.get('score')
            if value is None:
                raise ValueError("no score")
            label = fg.get('rating', _classify(value))
            return {'value': round(float(value), 1), 'label': label, 'available': True}
        except Exception:
            time.sleep(random.uniform(1, 3))
    # Fallback scraping
    try:
        soup = BeautifulSoup(requests.get('https://www.cnn.com/markets/fear-and-greed', headers=headers, timeout=5).text, 'html.parser')
        match = re.search(r'\b(\d+\.\d+)\b', soup.get_text())
        if match:
            value = float(match.group(1))
            return {'value': value, 'label': _classify(value), 'available': True}
    except Exception:
        pass
    return {'value': None, 'label': 'N/A', 'available': False}
