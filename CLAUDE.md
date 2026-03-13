# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

The first run will download the Hugging Face model (`cardiffnlp/twitter-roberta-base-sentiment-latest`) which is ~500MB.

## Running

```bash
python main.py daily    # single run — fetches news, sends email, exits (used by cron/launchd)
python main.py test     # single run in loop structure (for local testing)
python main.py          # continuous mode, fires daily at 09:00 via built-in scheduler
```

## Architecture

The app is a daily financial news digest pipeline:

1. **`news.py`** — fetches articles from NewsAPI (business + geopolitical keyword queries), deduplicates by title, runs NLP sentiment on each headline, formats an HTML newsletter
2. **`sentiment.py`** — fetches Crypto Fear & Greed (Alternative.me) and Stock Fear & Greed (CNN) indices, maps scores to investment posture
3. **`prices_getter.py`** — pulls BTC-USD and S&P 500 closing prices via yfinance, computes daily % change
4. **`email_sender.py`** — sends multi-recipient HTML email via Gmail SMTP
5. **`config.py`** — holds API keys, email credentials, and initializes the Hugging Face sentiment pipeline (loaded once at import time)
6. **`main.py`** — orchestrates all modules, builds the final email body (plain text + HTML), handles scheduling/mode switching

Data flow: `main.py` calls `news.py` → `sentiment.py` → `prices_getter.py` → `email_sender.py`.

## Configuration

All credentials and settings live in `config.py`:
- `NEWS_API_KEY` — NewsAPI key
- `EMAIL` / `PASSWORD` — Gmail sender credentials (PASSWORD is ROT13-encoded)
- `TO_EMAILS` — list of recipient addresses
- `SENTIMENT_PIPELINE` — instantiated at import; avoid re-importing unnecessarily as it triggers model loading
