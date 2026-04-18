import re
import json
import feedparser
import anthropic
from config import ANTHROPIC_API_KEY

_anthropic_client = None

def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client

def _strip_html(text):
    return re.sub(r'<[^>]+>', '', text or '').strip()

def _extract_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if 'image' in m.get('type', ''):
                return m.get('url', '')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href', enc.get('url', ''))
    return ''

BUSINESS_FEEDS = [
    ('BBC Business',  'https://feeds.bbci.co.uk/news/business/rss.xml'),
    ('CNBC',          'https://www.cnbc.com/id/100003114/device/rss/rss.html'),
    ('MarketWatch',   'https://feeds.marketwatch.com/marketwatch/topstories/'),
    ('The Guardian',  'https://www.theguardian.com/uk/business/rss'),
    ('Yahoo Finance', 'https://finance.yahoo.com/news/rssindex'),
]

GEO_FEEDS = [
    ('BBC World',    'https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('The Guardian', 'https://www.theguardian.com/world/rss'),
    ('Al Jazeera',   'https://www.aljazeera.com/xml/rss/all.xml'),
    ('Reuters',      'https://feeds.reuters.com/reuters/worldNews'),
]

def _fetch_rss(feeds, limit_per_feed=5):
    articles = []
    for source_name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit_per_feed]:
                title = _strip_html(entry.get('title', ''))
                desc  = _strip_html(entry.get('summary', entry.get('description', '')))
                if not title:
                    continue
                articles.append({
                    'title':       title,
                    'description': desc[:300],
                    'url':         entry.get('link', '#'),
                    'urlToImage':  _extract_image(entry),
                    'source':      {'name': source_name},
                })
        except Exception:
            continue
    return articles

def get_implication(title_desc):
    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": (
                    "Financial analyst. 1 sentence investment implication "
                    "(bullish/bearish/neutral + why):\n\n" + title_desc[:400]
                )
            }]
        )
        return response.content[0].text.strip()
    except Exception:
        return "Investment implication unavailable."

def get_morning_briefing(articles, prices, crypto, stock):
    """Calls Claude Sonnet to synthesise all news into a morning briefing."""
    headlines = "\n".join(
        f"- {a.get('title', '')} ({(a.get('source') or {}).get('name', '')})"
        for a in articles[:16]
    )

    def fmt(p, decimals=0):
        v, c = p.get('price'), p.get('change')
        if v is None: return 'N/A'
        sign = '+' if (c or 0) >= 0 else ''
        val  = f'{v:,.{decimals}f}' if decimals else f'{v:,.0f}'
        chg  = f' ({sign}{c:.1f}%)' if c is not None else ''
        return f'{val}{chg}'

    market = (
        f"BTC {fmt(prices.get('btc',{}))} | S&P500 {fmt(prices.get('spx',{}))} | "
        f"Gold {fmt(prices.get('gold',{}))} | Oil {fmt(prices.get('oil',{}), 2)} | "
        f"EUR/USD {fmt(prices.get('eurusd',{}), 4)}\n"
        f"Stock F&G {stock.get('value','N/A')}/100 ({stock.get('label','N/A')}) | "
        f"Crypto F&G {crypto.get('value','N/A')}/100 ({crypto.get('label','N/A')})"
    )

    prompt = f"""You are a senior financial analyst. No filler, no soft language. Every sentence must contain a specific asset, number, or causal link.

HEADLINES:
{headlines}

MARKET DATA:
{market}

Reply with valid JSON only (no markdown wrapper):
{{
  "big_picture": "2-3 sentences: what is moving markets today, why, and what it means for the week. Name specific assets and use the market data numbers.",
  "watch_list": [
    "Asset/story — specific directional implication with a reason (e.g. 'Gold +1.2% — safe-haven bid as...')",
    "Asset/story — specific directional implication with a reason",
    "Asset/story — specific directional implication with a reason"
  ],
  "posture": "RISK-ON",
  "posture_reason": "One sentence with a specific data point supporting the posture"
}}
posture must be exactly: RISK-ON, RISK-OFF, or NEUTRAL"""

    try:
        response = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        return json.loads(text)
    except Exception:
        return None

def _sentiment_badge(implication_text):
    t = implication_text.lower()
    if 'bullish' in t:
        return '#f0f7ec', '#2d5016', '#2d5016', '▲ Bullish'
    elif 'bearish' in t:
        return '#fdf0f0', '#8b2020', '#8b2020', '▼ Bearish'
    else:
        return '#f4edd8', '#5a4a3a', '#5a4a3a', '◆ Neutral'

def _article_card(art, implication):
    title    = art.get('title') or 'No title'
    raw_desc = art.get('description') or ''
    desc     = raw_desc[:240] + ('...' if len(raw_desc) > 240 else '')
    url      = art.get('url', '#')
    image_url = art.get('urlToImage', '')
    source   = (art.get('source') or {}).get('name', '')

    badge_bg, badge_border, badge_color, badge_label = _sentiment_badge(implication)

    img_html = (
        f'<img src="{image_url}" alt="" style="width:100%; max-height:320px; object-fit:cover; display:block;">'
        if image_url else ''
    )
    source_html = (
        f'<p style="font-family:Georgia,serif; font-size:10px; font-weight:700; color:#8b7355; letter-spacing:2px; text-transform:uppercase; margin:0 0 8px;">{source}</p>'
        if source else ''
    )

    return f"""
<div style="background:#fdf9f2; border:1px solid #e8dcc8; border-radius:4px; margin-bottom:16px; overflow:hidden;">
  {img_html}
  <div style="padding:20px 20px 16px;">
    {source_html}
    <h2 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; font-size:18px; font-weight:600; color:#1a1209; margin:0 0 10px; line-height:1.35;">{title}</h2>
    <p style="font-family:Georgia,serif; font-size:14px; color:#4a3728; line-height:1.7; margin:0 0 16px;">{desc}</p>
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
    <p style="font-family:Georgia,'Times New Roman',serif; font-size:13px; font-weight:700; color:{color}; letter-spacing:4px; text-transform:uppercase; margin:0;">{emoji}&nbsp;&nbsp;{title}&nbsp;&nbsp;{emoji}</p>
  </div>
</div>
"""

def get_news():
    business_raw = _fetch_rss(BUSINESS_FEEDS, limit_per_feed=5)
    geo_raw      = _fetch_rss(GEO_FEEDS,      limit_per_feed=5)

    seen = set()
    def dedupe(arts):
        out = []
        for a in arts:
            t = a.get('title', '')
            if t and t not in seen:
                seen.add(t)
                out.append(a)
        return out

    business_articles = dedupe(business_raw)[:6]
    geo_articles      = dedupe(geo_raw)[:6]
    all_articles      = business_articles + geo_articles

    if not all_articles:
        return "No news today.", "<p>No news available today.</p>", []

    summary = "The Coffee Post\n\n"
    for a in all_articles:
        summary += f"- {a.get('title')}\n"

    html = ''

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
