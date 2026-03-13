import sys
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from news import get_news
from email_sender import send_email
from sentiment import get_crypto_sentiment, get_stock_sentiment
from prices_getter import get_prices

def _fg_color(value):
    if value is None: return '#8b7355'
    if value < 25:   return '#8b2020'
    if value < 45:   return '#c05a1f'
    if value < 55:   return '#8b7a20'
    if value < 75:   return '#4a7a2d'
    return '#2d5016'

def _change_color(change):
    if change is None: return '#8b7355'
    return '#2d5016' if change >= 0 else '#8b2020'

def _price_str(p):
    if p is None: return 'N/A'
    return f'${p:,.0f}' if p >= 1000 else f'${p:.2f}'

def _change_str(change):
    if change is None: return 'N/A'
    sign = '+' if change >= 0 else ''
    return f'{sign}{change:.2f}%'

def build_email(news_html, prices, crypto, stock):
    now = datetime.now()
    date_str = now.strftime('%A, %B %d, %Y')

    btc = prices.get('btc', {})
    spx = prices.get('spx', {})
    crypto_val  = crypto.get('value')
    stock_val   = stock.get('value')
    stock_label = stock.get('label', 'N/A')
    crypto_label = crypto.get('label', 'N/A')

    stock_bar  = min(int(stock_val  or 0), 100)
    crypto_bar = min(int(crypto_val or 0), 100)

    btc_change   = btc.get('change')
    spx_change   = spx.get('change')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Coffee Post</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background-color:#ede6d6; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">

<div style="max-width:600px; margin:0 auto; padding:24px 12px;">

  <!-- ═══════════════════════════════════════ -->
  <!-- MASTHEAD                                -->
  <!-- ═══════════════════════════════════════ -->
  <div style="background:#fdf9f2; border-top:4px solid #1a1209; padding:28px 28px 20px;">

    <p style="font-family:Georgia,'Times New Roman',serif; font-size:10px; font-weight:700; letter-spacing:5px; text-transform:uppercase; color:#8b7355; text-align:center; margin:0 0 14px;">Your Morning Briefing</p>

    <div style="border-top:1px solid #1a1209; border-bottom:1px solid #1a1209; padding:14px 0; text-align:center; margin-bottom:14px;">
      <h1 style="font-family:'Playfair Display', Georgia, 'Times New Roman', serif; font-size:44px; font-weight:900; color:#1a1209; margin:0; letter-spacing:-1px; line-height:1;">The Coffee Post</h1>
    </div>

    <p style="font-family:Georgia,'Times New Roman',serif; font-size:12px; color:#8b7355; text-align:center; margin:0 0 10px; font-style:italic; letter-spacing:0.5px;">Financial Intelligence, Every Morning</p>

    <div style="border-top:1px solid #c8b89a; padding-top:12px; text-align:center;">
      <p style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a; letter-spacing:0.3px; margin:0 0 6px;">{date_str}</p>
      <p style="font-family:Georgia,serif; font-size:11px; color:#8b7355; letter-spacing:1px; margin:0;">Markets Edition &nbsp;·&nbsp; Vol. I</p>
    </div>

  </div>

  <!-- ═══════════════════════════════════════ -->
  <!-- MARKET TICKER BAND                      -->
  <!-- ═══════════════════════════════════════ -->
  <div style="background:#1a1209; padding:20px 24px;">

    <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:4px; text-transform:uppercase; color:#8b7355; margin:0 0 14px; text-align:center;">Today's Markets</p>

    <!-- BTC + S&P row -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px;">
      <tr>
        <td width="48%" style="vertical-align:top; padding-right:8px;">
          <div style="border:1px solid #3d2b1f; padding:14px 12px; text-align:center;">
            <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#c8920a; margin:0 0 8px;">Bitcoin</p>
            <p style="font-family:'Playfair Display',Georgia,serif; font-size:22px; font-weight:700; color:#fdf9f2; margin:0 0 4px;">{_price_str(btc.get('price'))}</p>
            <p style="font-family:Georgia,serif; font-size:13px; font-weight:700; color:{_change_color(btc_change)}; margin:0;">{_change_str(btc_change)}</p>
          </div>
        </td>
        <td width="4%"></td>
        <td width="48%" style="vertical-align:top; padding-left:8px;">
          <div style="border:1px solid #3d2b1f; padding:14px 12px; text-align:center;">
            <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#c8920a; margin:0 0 8px;">S&amp;P 500</p>
            <p style="font-family:'Playfair Display',Georgia,serif; font-size:22px; font-weight:700; color:#fdf9f2; margin:0 0 4px;">{_price_str(spx.get('price'))}</p>
            <p style="font-family:Georgia,serif; font-size:13px; font-weight:700; color:{_change_color(spx_change)}; margin:0;">{_change_str(spx_change)}</p>
          </div>
        </td>
      </tr>
    </table>

    <!-- Fear & Greed -->
    <div style="border:1px solid #3d2b1f; padding:14px 16px;">
      <p style="font-family:Georgia,serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#c8920a; margin:0 0 14px; text-align:center;">Fear &amp; Greed Index</p>

      <div style="margin-bottom:12px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:5px;">
          <tr>
            <td><span style="font-family:Georgia,serif; font-size:11px; color:#c8b89a;">Stocks</span></td>
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(stock_val)};">{stock_val or 'N/A'}/100 &mdash; {stock_label}</span></td>
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
            <td style="text-align:right;"><span style="font-family:Georgia,serif; font-size:11px; font-weight:700; color:{_fg_color(crypto_val)};">{crypto_val or 'N/A'}/100 &mdash; {crypto_label}</span></td>
          </tr>
        </table>
        <div style="background:#3d2b1f; height:6px; border-radius:1px; overflow:hidden;">
          <div style="background:{_fg_color(crypto_val)}; height:6px; width:{crypto_bar}%;"></div>
        </div>
      </div>
    </div>

  </div>

  <!-- ═══════════════════════════════════════ -->
  <!-- NEWS CONTENT                            -->
  <!-- ═══════════════════════════════════════ -->
  <div style="background:#ede6d6; padding:4px 0 8px;">
    {news_html}
  </div>

  <!-- ═══════════════════════════════════════ -->
  <!-- FOOTER                                  -->
  <!-- ═══════════════════════════════════════ -->
  <div style="background:#1a1209; border-top:3px solid #c8920a; padding:24px 28px; text-align:center;">
    <p style="font-family:'Playfair Display', Georgia, serif; font-size:16px; color:#c8920a; margin:0 0 6px; font-style:italic;">The Coffee Post</p>
    <p style="font-family:Georgia,serif; font-size:11px; color:#5a4a3a; margin:0 0 4px; letter-spacing:0.3px;">Powered by NewsAPI &amp; Claude AI</p>
    <p style="font-family:Georgia,serif; font-size:10px; color:#3d2b1f; margin:0; letter-spacing:0.3px;">For informational purposes only &mdash; not financial advice.</p>
  </div>

</div>
</body>
</html>"""

def run_and_send():
    print(f"Running {datetime.now()}")
    news_summary, news_html, _ = get_news()
    prices = get_prices()
    crypto = get_crypto_sentiment()
    stock  = get_stock_sentiment()

    html = build_email(news_html, prices, crypto, stock)

    btc = prices.get('btc', {})
    spx = prices.get('spx', {})
    summary  = news_summary
    summary += f"\nMarkets: BTC {_price_str(btc.get('price'))} ({_change_str(btc.get('change'))}) | "
    summary += f"S&P500 {_price_str(spx.get('price'))} ({_change_str(spx.get('change'))})\n"
    summary += f"Stock F&G: {stock.get('value','N/A')} ({stock.get('label','N/A')}) | "
    summary += f"Crypto F&G: {crypto.get('value','N/A')} ({crypto.get('label','N/A')})\n"

    print("Sending email...")
    send_email(summary, html)
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
