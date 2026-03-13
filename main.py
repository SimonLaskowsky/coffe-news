import sys
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from news import get_news, get_morning_briefing
from email_sender import send_email
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

def _price_cell(label, p, color, decimals=0):
    price = p.get('price')
    change = p.get('change')
    ps = _price_str(price, decimals) if decimals else _price_str(price)
    cs = _chg_str(change)
    cc = _chg_color(change)
    return f"""
<td style="vertical-align:top; padding:4px;">
  <div style="border:1px solid #3d2b1f; padding:12px 10px; text-align:center;">
    <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:{color}; margin:0 0 6px;">{label}</p>
    <p style="font-family:'Playfair Display',Georgia,serif; font-size:17px; font-weight:700; color:#fdf9f2; margin:0 0 3px;">{ps}</p>
    <p style="font-family:Georgia,serif; font-size:12px; font-weight:700; color:{cc}; margin:0;">{cs}</p>
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
<body style="margin:0; padding:0; background-color:#ede6d6; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
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
  <div style="background:#1a1209; padding:20px 20px 18px;">
    <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:4px; text-transform:uppercase; color:#8b7355; margin:0 0 12px; text-align:center;">Today's Markets</p>

    <!-- Row 1: BTC + S&P -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;">
      <tr>
        {_price_cell('Bitcoin',  btc,  '#c8920a')}
        {_price_cell('S&amp;P 500', spx, '#60a5fa')}
      </tr>
    </table>

    <!-- Row 2: Gold + Oil + EUR/USD -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:14px;">
      <tr>
        {_price_cell('Gold',    gold,   '#d4af37')}
        {_price_cell('Oil WTI', oil,    '#9ca3af', decimals=2)}
        {_price_cell('EUR/USD', eurusd, '#86efac', decimals=4)}
      </tr>
    </table>

    <!-- Fear & Greed -->
    <div style="border:1px solid #3d2b1f; padding:14px 16px;">
      <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#c8920a; margin:0 0 14px; text-align:center;">Fear &amp; Greed Index</p>
      <div style="margin-bottom:12px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:5px;">
          <tr>
            <td><span style="font-family:Georgia,serif; font-size:11px; color:#c8b89a;">Stocks</span></td>
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(stock_val)};">{stock_val or 'N/A'}/100 &mdash; {stock.get('label','N/A')}</span></td>
          </tr>
        </table>
        <div style="background:#3d2b1f; height:6px; border-radius:1px; overflow:hidden;">
          <div style="background:{_fg_color(stock_val)}; height:6px; width:{stock_bar}%;"></div>
        </div>
      </div>
      <div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:5px;">
          <tr>
            <td><span style="font-family:Georgia,serif; font-size:11px; color:#c8b89a;">Crypto</span></td>
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(crypto_val)};">{crypto_val or 'N/A'}/100 &mdash; {crypto.get('label','N/A')}</span></td>
          </tr>
        </table>
        <div style="background:#3d2b1f; height:6px; border-radius:1px; overflow:hidden;">
          <div style="background:{_fg_color(crypto_val)}; height:6px; width:{crypto_bar}%;"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- MORNING BRIEFING + NEWS -->
  <div style="background:#ede6d6; padding:16px 4px 8px;">
    {briefing_block}
    {news_html}
  </div>

  <!-- FOOTER -->
  <div style="background:#1a1209; border-top:3px solid #c8920a; padding:24px 28px; text-align:center;">
    <p style="font-family:'Playfair Display',Georgia,serif; font-size:16px; color:#c8920a; margin:0 0 6px; font-style:italic;">The Coffee Post</p>
    <p style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a; margin:0 0 4px;">Powered by NewsAPI &amp; Claude AI</p>
    <p style="font-family:Georgia,serif; font-size:10px; color:#3d2b1f; margin:0;">For informational purposes only &mdash; not financial advice.</p>
  </div>

</div>
</body>
</html>"""

# ── runner ────────────────────────────────────────────────────────────────────

def run_and_send():
    print(f"Running {datetime.now()}")
    news_summary, news_html, articles = get_news()
    prices  = get_prices()
    crypto  = get_crypto_sentiment()
    stock   = get_stock_sentiment()
    briefing = get_morning_briefing(articles, prices, crypto, stock)

    html = build_email(news_html, briefing, prices, crypto, stock)
    send_email(news_summary, html)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("test", "daily"):
        run_and_send()
    else:
        schedule.every().day.at("09:00").do(run_and_send)
        print("Running in background, waiting for 09:00...")
        while True:
            schedule.run_pending()
            time.sleep(60)
