import sys
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from news import get_news, get_morning_briefing
from email_sender import send_email
from config import EMAIL
from sentiment import get_crypto_sentiment, get_stock_sentiment
from prices_getter import get_prices

# ── helpers ──────────────────────────────────────────────────────────────────

def _fg_color(v):
    if v is None:  return '#8b7355'
    if v < 25:     return '#8b2020'
    if v < 45:     return '#c05a1f'
    if v < 55:     return '#8b7a20'
    if v < 75:     return '#4a7a2d'
    return '#2d5016'

def _chg_color(c):
    if c is None: return '#8b7355'
    return '#2d5016' if c >= 0 else '#8b2020'

def _price_str(p, decimals=0):
    if p is None: return 'N/A'
    if decimals:  return f'{p:,.{decimals}f}'
    return f'${p:,.0f}' if p >= 100 else f'${p:.2f}'

def _chg_str(c):
    if c is None: return ''
    return f'{"+" if c >= 0 else ""}{c:.2f}%'

def _price_cell(label, p, decimals=0):
    price = p.get('price')
    change = p.get('change')
    week_change = p.get('week_change')
    month_change = p.get('month_change')
    ps = _price_str(price, decimals) if decimals else _price_str(price)
    cs = _chg_str(change)
    cc = _chg_color(change)
    wc_str = f'w: {_chg_str(week_change)}' if week_change is not None else ''
    mc_str = f'm: {_chg_str(month_change)}' if month_change is not None else ''
    extra_parts = [x for x in [wc_str, mc_str] if x]
    extra = (
        f'<p style="font-family:Georgia,serif; font-size:9px; color:#8b7355; margin:4px 0 0;">'
        + ' &nbsp;·&nbsp; '.join(extra_parts) + '</p>'
    ) if extra_parts else ''
    return f"""
<td style="vertical-align:top; padding:4px;">
  <div style="border:1px solid #e8dcc8; border-top:2px solid #1a1209; padding:12px 10px; text-align:center; background:#fdf9f2;">
    <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#8b7355; margin:0 0 6px;">{label}</p>
    <p style="font-family:'Playfair Display',Georgia,serif; font-size:17px; font-weight:700; color:#1a1209; margin:0 0 3px;">{ps}</p>
    <p style="font-family:Georgia,serif; font-size:12px; font-weight:700; color:{cc}; margin:0;">{cs}</p>
    {extra}
  </div>
</td>"""


def _briefing_html(briefing):
    if not briefing:
        return ''

    posture = briefing.get('posture', 'NEUTRAL')
    if posture == 'RISK-ON':
        p_bg, p_color, p_border = '#f0f7ec', '#2d5016', '#2d5016'
    elif posture == 'RISK-OFF':
        p_bg, p_color, p_border = '#fdf0f0', '#8b2020', '#8b2020'
    else:
        p_bg, p_color, p_border = '#f4edd8', '#5a4a3a', '#8b7355'

    watch_items = ''.join(
        f'<p style="font-family:Georgia,serif; font-size:13px; color:#3d2b1f; line-height:1.6; margin:0 0 8px; padding-left:12px; border-left:2px solid #e8dcc8;">• {item}</p>'
        for item in briefing.get('watch_list', [])
    )

    return f"""
<div style="background:#fdf9f2; border:1px solid #c8b89a; border-left:4px solid #c8920a; margin-bottom:4px; padding:22px 22px 18px;">
  <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:4px; text-transform:uppercase; color:#c8920a; margin:0 0 18px;">☕&nbsp; Morning Briefing</p>

  <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#8b7355; margin:0 0 8px;">The Big Picture</p>
  <p style="font-family:Georgia,serif; font-size:14px; color:#3d2b1f; line-height:1.75; margin:0 0 20px;">{briefing.get('big_picture','')}</p>

  <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#8b7355; margin:0 0 10px;">Watch List</p>
  {watch_items}

  <div style="margin-top:16px; padding:10px 14px; background:{p_bg}; border-left:3px solid {p_border};">
    <span style="font-family:Georgia,serif; font-size:10px; font-weight:700; color:{p_color}; letter-spacing:2px; text-transform:uppercase;">▶&nbsp;{posture}</span>
    <span style="font-family:Georgia,serif; font-size:13px; color:{p_color};"> — {briefing.get('posture_reason','')}</span>
  </div>
</div>
"""

# ── email builder ─────────────────────────────────────────────────────────────

def build_email(news_html, briefing, prices, crypto, stock):
    date_str = datetime.now().strftime('%A, %B %d, %Y')

    btc    = prices.get('btc',    {})
    spx    = prices.get('spx',    {})
    gold   = prices.get('gold',   {})
    oil    = prices.get('oil',    {})
    eurusd = prices.get('eurusd', {})

    stock_val  = stock.get('value')
    crypto_val = crypto.get('value')
    stock_bar  = min(int(stock_val  or 0), 100)
    crypto_bar = min(int(crypto_val or 0), 100)

    briefing_block = _briefing_html(briefing)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Coffee Post</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background-color:#f5f0e8; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:600px; margin:0 auto; padding:24px 12px;">

  <!-- MASTHEAD -->
  <div style="background:#fdf9f2; border-top:4px solid #1a1209; padding:28px 28px 20px;">
    <p style="font-family:Georgia,'Times New Roman',serif; font-size:10px; font-weight:700; letter-spacing:5px; text-transform:uppercase; color:#8b7355; text-align:center; margin:0 0 14px;">Your Morning Briefing</p>
    <div style="border-top:1px solid #1a1209; border-bottom:1px solid #1a1209; padding:14px 0; text-align:center; margin-bottom:14px;">
      <h1 style="font-family:'Playfair Display',Georgia,'Times New Roman',serif; font-size:44px; font-weight:900; color:#1a1209; margin:0; letter-spacing:-1px; line-height:1;">The Coffee Post</h1>
    </div>
    <p style="font-family:Georgia,'Times New Roman',serif; font-size:12px; color:#8b7355; text-align:center; margin:0 0 10px; font-style:italic; letter-spacing:0.5px;">Financial Intelligence, Every Morning</p>
    <div style="border-top:1px solid #c8b89a; padding-top:12px; text-align:center;">
      <p style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a; letter-spacing:0.3px; margin:0 0 6px;">{date_str}</p>
      <p style="font-family:Georgia,serif; font-size:11px; color:#8b7355; letter-spacing:1px; margin:0;">Markets Edition &nbsp;·&nbsp; Vol. I</p>
    </div>
  </div>

  <!-- MARKET BAND -->
  <div style="background:#fdf9f2; border:1px solid #e8dcc8; border-top:none; padding:20px 20px 18px;">
    <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:4px; text-transform:uppercase; color:#8b7355; margin:0 0 12px; text-align:center;">Today's Markets</p>

    <!-- Row 1: BTC + S&P -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;">
      <tr>
        {_price_cell('Bitcoin',  btc)}
        {_price_cell('S&amp;P 500', spx)}
      </tr>
    </table>

    <!-- Row 2: Gold + Oil + EUR/USD -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:14px;">
      <tr>
        {_price_cell('Gold',    gold)}
        {_price_cell('Oil WTI', oil,    decimals=2)}
        {_price_cell('EUR/USD', eurusd, decimals=4)}
      </tr>
    </table>

    <!-- Fear & Greed -->
    <div style="border:1px solid #e8dcc8; border-top:2px solid #1a1209; padding:14px 16px; background:#fdf9f2;">
      <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#8b7355; margin:0 0 14px; text-align:center;">Fear &amp; Greed Index</p>
      <div style="margin-bottom:12px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:5px;">
          <tr>
            <td><span style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a;">Stocks</span></td>
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(stock_val)};">{stock_val or 'N/A'}/100 &mdash; {stock.get('label','N/A')}</span></td>
          </tr>
        </table>
        <div style="background:#e8dcc8; height:6px; border-radius:1px; overflow:hidden;">
          <div style="background:{_fg_color(stock_val)}; height:6px; width:{stock_bar}%;"></div>
        </div>
      </div>
      <div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:5px;">
          <tr>
            <td><span style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a;">Crypto</span></td>
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(crypto_val)};">{crypto_val or 'N/A'}/100 &mdash; {crypto.get('label','N/A')}</span></td>
          </tr>
        </table>
        <div style="background:#e8dcc8; height:6px; border-radius:1px; overflow:hidden;">
          <div style="background:{_fg_color(crypto_val)}; height:6px; width:{crypto_bar}%;"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- MORNING BRIEFING + NEWS -->
  <div style="background:#fdf9f2; border:1px solid #e8dcc8; border-top:none; padding:16px 4px 8px;">
    {briefing_block}
    {news_html}
  </div>

  <!-- FOOTER -->
  <div style="background:#fdf9f2; border:1px solid #e8dcc8; border-top:3px solid #1a1209; padding:24px 28px; text-align:center;">
    <p style="font-family:'Playfair Display',Georgia,serif; font-size:16px; color:#1a1209; margin:0 0 6px; font-style:italic;">The Coffee Post</p>
    <p style="font-family:Georgia,serif; font-size:11px; color:#8b7355; margin:0 0 4px;">Powered by Claude AI</p>
    <p style="font-family:Georgia,serif; font-size:10px; color:#8b7355; margin:0;">For informational purposes only &mdash; not financial advice.</p>
  </div>

</div>
</body>
</html>"""

# ── runner ────────────────────────────────────────────────────────────────────

def run_and_send(test=False):
    print(f"Running {datetime.now()}" + (" [TEST]" if test else ""))
    news_summary, news_html, articles = get_news()
    prices  = get_prices()
    crypto  = get_crypto_sentiment()
    stock   = get_stock_sentiment()
    briefing = get_morning_briefing(articles, prices, crypto, stock)

    html = build_email(news_html, briefing, prices, crypto, stock)
    send_email(news_summary, html, recipients=[EMAIL] if test else None)
    print("Done.")

def run_preview():
    import tempfile, webbrowser
    from news import _article_card, _section_header
    mock_articles = [
        {'title': 'Federal Reserve Holds Rates Steady Amid Inflation Concerns', 'description': 'The Federal Reserve kept interest rates unchanged at its latest meeting, signalling caution as inflation remains above the 2% target despite recent cooling in consumer prices.', 'url': '#', 'urlToImage': 'https://picsum.photos/seed/fed/600/190', 'source': {'name': 'Reuters'}},
        {'title': 'S&P 500 Hits New Record High Driven by Tech Surge', 'description': 'The benchmark index climbed 1.4% to an all-time high, led by gains in semiconductor stocks after a stronger-than-expected earnings report from the sector.', 'url': '#', 'urlToImage': 'https://picsum.photos/seed/spx/600/190', 'source': {'name': 'CNBC'}},
        {'title': 'Oil Prices Slip as OPEC Output Rises Faster Than Expected', 'description': 'Crude futures fell 2.1% after OPEC data showed member nations pumping above agreed quotas, adding supply pressure to a market already weighing demand uncertainty from China.', 'url': '#', 'urlToImage': 'https://picsum.photos/seed/oil/600/190', 'source': {'name': 'MarketWatch'}},
        {'title': 'Tensions Escalate in South China Sea After Naval Incident', 'description': 'A confrontation between Chinese and Philippine vessels near disputed reefs has raised concerns among investors exposed to Asian markets, with risk-off sentiment spreading to regional currencies.', 'url': '#', 'urlToImage': 'https://picsum.photos/seed/geo/600/190', 'source': {'name': 'BBC World'}},
        {'title': 'Germany Narrowly Avoids Recession as Factory Output Rebounds', 'description': 'Industrial production rose 0.8% in the latest month, beating forecasts and easing fears of a second consecutive quarterly contraction in Europe\'s largest economy.', 'url': '#', 'urlToImage': 'https://picsum.photos/seed/ger/600/190', 'source': {'name': 'The Guardian'}},
    ]
    mock_briefing = {
        'big_picture': 'Risk appetite is cautiously positive as the Fed holds steady and tech earnings beat expectations, pushing SPX to 5,480 (+1.4%). Bond yields edged down 6bps to 4.31%, reflecting a soft-landing narrative. The main wildcard is oil — OPEC oversupply is capping energy stocks and pressuring CAD and NOK.',
        'watch_list': [
            'SPX at 5,480 (+1.4%) — momentum intact above 5,400 support; watch Friday CPI for continuation',
            'Crude -2.1% to $78.40 — OPEC quota breach adds downside pressure; break of $77 targets $74',
            'South China Sea — risk-off trigger if incident escalates; AUD and Asian EM FX most exposed',
        ],
        'posture': 'RISK-ON',
        'posture_reason': 'SPX breakout + Fed pause + falling yields outweigh oil and geopolitical drag.',
    }
    mock_prices = {
        'btc':    {'price': 68420, 'change': 2.3,  'week_change': 5.1,  'month_change': -8.4},
        'spx':    {'price': 5480,  'change': 1.4,  'week_change': 2.0,  'month_change': 3.7},
        'gold':   {'price': 2341,  'change': -0.3, 'week_change': 1.2,  'month_change': 4.9},
        'oil':    {'price': 78.40, 'change': -2.1, 'week_change': -3.5, 'month_change': -1.2},
        'eurusd': {'price': 1.0823,'change': 0.1,  'week_change': -0.4, 'month_change': 0.8},
    }
    mock_crypto = {'value': 62, 'label': 'Greed'}
    mock_stock  = {'value': 71, 'label': 'Greed'}

    news_html  = _section_header('◆', 'Markets &amp; Business', '#1e3a6e', '#1e3a6e')
    news_html += ''.join(_article_card(a, 'Bullish — strong earnings momentum supports further upside.') for a in mock_articles[:3])
    news_html += _section_header('◆', 'World Affairs', '#4a2d6b', '#4a2d6b')
    news_html += ''.join(_article_card(a, 'Bearish — geopolitical risk adds volatility to regional assets.') for a in mock_articles[3:])

    html = build_email(news_html, mock_briefing, mock_prices, mock_crypto, mock_stock)
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
        f.write(html)
        path = f.name
    webbrowser.open(f'file://{path}')
    print(f"Preview opened: {path}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        run_preview()
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        run_and_send(test=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "daily":
        run_and_send()
    else:
        schedule.every().day.at("07:00").do(run_and_send)
        print("Running in background, waiting for 07:00...")
        while True:
            schedule.run_pending()
            time.sleep(60)
