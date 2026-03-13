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
            hist = yf.Ticker(ticker).history(period='5d')
            if len(hist) >= 1:
                close = hist['Close'].iloc[-1]
                open_ = hist['Open'].iloc[-1]
                change = ((close - open_) / open_) * 100
                result[key] = {'price': float(close), 'change': float(change)}
            else:
                result[key] = {'price': None, 'change': None}
        except Exception:
            result[key] = {'price': None, 'change': None}
    return result
