import yfinance as yf

def get_prices():
    """Returns BTC and S&P 500 price data as a dict."""
    try:
        btc_hist = yf.Ticker('BTC-USD').history(period='1d')
        btc_close = btc_hist['Close'].iloc[-1]
        btc_change = ((btc_close - btc_hist['Open'].iloc[0]) / btc_hist['Open'].iloc[0]) * 100

        spx_hist = yf.Ticker('^GSPC').history(period='1d')
        spx_close = spx_hist['Close'].iloc[-1]
        spx_change = ((spx_close - spx_hist['Open'].iloc[0]) / spx_hist['Open'].iloc[0]) * 100

        return {
            'btc': {'price': btc_close, 'change': btc_change},
            'spx': {'price': spx_close, 'change': spx_change},
        }
    except Exception:
        return {
            'btc': {'price': None, 'change': None},
            'spx': {'price': None, 'change': None},
        }
