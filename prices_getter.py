import yfinance as yf

TICKERS = {
    'btc':    'BTC-USD',
    'spx':    '^GSPC',
    'gold':   'GC=F',
    'oil':    'CL=F',
    'eurusd': 'EURUSD=X',
}

def get_prices():
    result = {}
    for key, ticker in TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period='35d')
            if len(hist) >= 1:
                close = hist['Close'].iloc[-1]
                open_ = hist['Open'].iloc[-1]
                change = ((close - open_) / open_) * 100
                week_change = None
                if len(hist) >= 6:
                    week_change = ((close - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100
                month_change = None
                if len(hist) >= 23:
                    month_change = ((close - hist['Close'].iloc[-23]) / hist['Close'].iloc[-23]) * 100
                result[key] = {
                    'price': float(close),
                    'change': float(change),
                    'week_change': float(week_change) if week_change is not None else None,
                    'month_change': float(month_change) if month_change is not None else None,
                }
            else:
                result[key] = {'price': None, 'change': None, 'week_change': None, 'month_change': None}
        except Exception:
            result[key] = {'price': None, 'change': None, 'week_change': None, 'month_change': None}
    return result
