import requests
import anthropic
from datetime import datetime, timedelta
from config import NEWS_API_KEY, ANTHROPIC_API_KEY

_anthropic_client = None

def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client

def get_implication(title_desc):
    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": (
                    "You are a financial analyst. In 1-2 sentences, give the investment implication "
                    "(bullish/bearish/neutral and why) of this news:\n\n" + title_desc[:500]
                )
            }]
        )
        return response.content[0].text.strip()
    except Exception:
        return "Investment implication unavailable."

def _sentiment_badge(implication_text):
    t = implication_text.lower()
    if 'bullish' in t:
        return '#f0f7ec', '#2d5016', '#2d5016', '▲ Bullish'
    elif 'bearish' in t:
        return '#fdf0f0', '#8b2020', '#8b2020', '▼ Bearish'
    else:
        return '#f4edd8', '#5a4a3a', '#5a4a3a', '◆ Neutral'

def _article_card(art, implication):
    title = art.get('title') or 'No title'
    raw_desc = art.get('description') or ''
    desc = raw_desc[:240] + ('...' if len(raw_desc) > 240 else '')
    url = art.get('url', '#')
    image_url = art.get('urlToImage', '')
    source = (art.get('source') or {}).get('name', '')

    badge_bg, badge_border, badge_color, badge_label = _sentiment_badge(implication)

    img_html = ''
    if image_url:
        img_html = f'<img src="{image_url}" alt="" style="width:100%; height:190px; object-fit:cover; display:block;">'

    source_html = ''
    if source:
        source_html = f'<p style="font-family:Georgia,serif; font-size:10px; font-weight:700; color:#8b7355; letter-spacing:2px; text-transform:uppercase; margin:0 0 8px;">{source}</p>'

    return f"""
<div style="background:#fdf9f2; border:1px solid #e8dcc8; border-radius:4px; margin-bottom:16px; overflow:hidden;">
  {img_html}
  <div style="padding:20px 20px 16px;">
    {source_html}
    <h2 style="font-family:'Playfair Display', Georgia, 'Times New Roman', serif; font-size:18px; font-weight:700; color:#1a1209; margin:0 0 10px; line-height:1.4;">{title}</h2>
    <p style="font-family:Georgia, serif; font-size:14px; color:#4a3728; line-height:1.7; margin:0 0 16px;">{desc}</p>
    <div style="border-top:1px solid #e8dcc8; padding-top:14px; margin-bottom:4px;">
      <span style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; font-size:10px; font-weight:700; padding:4px 12px; letter-spacing:1px; text-transform:uppercase;">{badge_label}</span>
    </div>
    <div style="padding-top:10px;">
      <a href="{url}" style="font-family:Georgia,serif; font-size:12px; color:#6b3a2a; text-decoration:none; letter-spacing:0.5px; font-style:italic;">Read full story →</a>
    </div>
    <p style="font-family:Georgia,serif; font-size:12px; color:#7a6555; line-height:1.6; margin:10px 0 0; font-style:italic;">{implication}</p>
  </div>
</div>
"""

def _section_header(emoji, title, color, border_color):
    return f"""
<div style="margin:28px 0 16px; text-align:center;">
  <div style="border-top:2px solid {border_color}; border-bottom:1px solid {border_color}; padding:8px 0;">
    <p style="font-family:'Playfair Display', Georgia, 'Times New Roman', serif; font-size:13px; font-weight:700; color:{color}; letter-spacing:4px; text-transform:uppercase; margin:0;">{emoji}&nbsp;&nbsp;{title}&nbsp;&nbsp;{emoji}</p>
  </div>
</div>
"""

def get_news():
    sources = 'reuters,bloomberg,bbc-news,ap-news,cnn,the-guardian'
    from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    business_keywords = 'inflation OR fed OR GDP OR recession OR "stock market" OR "interest rates" OR bitcoin OR crypto OR oil OR gold OR tariff OR "market crash" OR "trade war"'
    geo_keywords = 'sanctions OR NATO OR war OR conflict OR elections OR Ukraine OR Russia OR "Middle East" OR China OR "trade tensions" OR diplomacy'

    def fetch(url):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get('status') == 'ok':
                return data.get('articles', [])
        except Exception:
            pass
        return []

    hot_articles      = fetch(f'https://newsapi.org/v2/top-headlines?category=business&pageSize=4&apiKey={NEWS_API_KEY}')[:4]
    business_articles = fetch(f'https://newsapi.org/v2/everything?q={business_keywords}&from={from_date}&sortBy=popularity&pageSize=8&language=en&apiKey={NEWS_API_KEY}')[:6]
    geo_articles      = fetch(f'https://newsapi.org/v2/everything?q={geo_keywords}&from={from_date}&sortBy=popularity&pageSize=8&language=en&apiKey={NEWS_API_KEY}')[:6]

    seen = set()
    def dedupe(arts):
        out = []
        for a in arts:
            t = a.get('title', '')
            if t and t not in seen:
                seen.add(t)
                out.append(a)
        return out

    hot_articles      = dedupe(hot_articles)
    business_articles = dedupe(business_articles)
    geo_articles      = dedupe(geo_articles)

    all_articles = hot_articles + business_articles + geo_articles
    if not all_articles:
        return "No news today.", "<p>No news available today.</p>", []

    summary = f"The Coffee Post — {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for art in all_articles:
        impl = get_implication((art.get('title') or '') + ' ' + (art.get('description') or ''))
        summary += f"- {art.get('title')}\n  {impl}\n\n"

    html = ''

    if hot_articles:
        html += _section_header('◆', 'Breaking News', '#8b2020', '#8b2020')
        for art in hot_articles:
            impl = get_implication((art.get('title') or '') + ' ' + (art.get('description') or ''))
            html += _article_card(art, impl)

    if business_articles:
        html += _section_header('◆', 'Markets &amp; Business', '#1e3a6e', '#1e3a6e')
        for art in business_articles:
            impl = get_implication((art.get('title') or '') + ' ' + (art.get('description') or ''))
            html += _article_card(art, impl)

    if geo_articles:
        html += _section_header('◆', 'World Affairs', '#4a2d6b', '#4a2d6b')
        for art in geo_articles:
            impl = get_implication((art.get('title') or '') + ' ' + (art.get('description') or ''))
            html += _article_card(art, impl)

    return summary, html, all_articles
