"""
YFinance Data Collector
backend/scrapers/yfinance_collector.py

Fetches real stock market data from Yahoo Finance.
Uses yf.download() for bulk price data (single request, no rate limits).
Uses .fast_info for metadata (with rate limiting and retries).
"""
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from backend.utils import log


class YFinanceCollector:
    """Collect real stock data from Yahoo Finance"""

    def get_multiple_stocks(self, symbols, period="1y", interval="1d"):
        """
        Fetch historical OHLCV data for multiple stocks using yf.download().
        This is a single bulk request — fast and avoids rate limits.

        Args:
            symbols: List of ticker symbols
            period: '1mo', '3mo', '6mo', '1y', '2y', '5y'
            interval: '1d', '1wk', '1mo'

        Returns:
            DataFrame with columns: symbol, Date, Open, High, Low, Close, Volume
        """
        log.info(f"Downloading data for {len(symbols)} stocks (period={period})...")

        try:
            # yf.download handles multiple tickers in one request
            raw = yf.download(
                tickers=symbols,
                period=period,
                interval=interval,
                group_by='ticker',
                auto_adjust=True,
                threads=True,
            )

            if raw.empty:
                log.error("yf.download returned empty DataFrame")
                return pd.DataFrame()

            all_data = []

            # Handle single vs multiple tickers (different DataFrame structure)
            if len(symbols) == 1:
                sym = symbols[0]
                df = raw.copy()
                df = df.reset_index()
                df['symbol'] = sym
                df = df.rename(columns={'index': 'Date'})
                if 'Date' not in df.columns and 'Datetime' in df.columns:
                    df = df.rename(columns={'Datetime': 'Date'})
                all_data.append(df)
            else:
                for sym in symbols:
                    try:
                        if sym not in raw.columns.get_level_values(0):
                            log.warning(f"No data for {sym} in download result")
                            continue

                        df = raw[sym].copy()
                        df = df.dropna(how='all')
                        if df.empty:
                            log.warning(f"Empty data for {sym}")
                            continue

                        df = df.reset_index()
                        df['symbol'] = sym

                        # Rename Date column if needed
                        if 'Date' not in df.columns:
                            date_col = [c for c in df.columns if 'date' in c.lower() or 'Date' in str(c)]
                            if date_col:
                                df = df.rename(columns={date_col[0]: 'Date'})

                        all_data.append(df)
                    except Exception as e:
                        log.warning(f"Error processing {sym}: {e}")
                        continue

            if not all_data:
                log.error("No data extracted from download")
                return pd.DataFrame()

            combined = pd.concat(all_data, ignore_index=True)

            # Standardize columns
            col_map = {}
            for col in combined.columns:
                cl = str(col).lower()
                if cl == 'open': col_map[col] = 'Open'
                elif cl == 'high': col_map[col] = 'High'
                elif cl == 'low': col_map[col] = 'Low'
                elif cl == 'close': col_map[col] = 'Close'
                elif cl == 'volume': col_map[col] = 'Volume'
            combined = combined.rename(columns=col_map)

            # Keep only needed columns
            keep = ['symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            available = [c for c in keep if c in combined.columns]
            combined = combined[available]

            # Remove timezone if present
            if combined['Date'].dt.tz is not None:
                combined['Date'] = combined['Date'].dt.tz_localize(None)

            # Drop rows with no close price
            combined = combined.dropna(subset=['Close'])

            log.info(f"✓ Downloaded {len(combined)} rows for {combined['symbol'].nunique()} stocks")
            log.info(f"  Date range: {combined['Date'].min().date()} to {combined['Date'].max().date()}")

            return combined

        except Exception as e:
            log.error(f"yf.download failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_stock_info(self, symbol, retries=3):
        """
        Get stock metadata using .fast_info (avoids rate limits).
        Falls back gracefully if Yahoo blocks the request.

        Returns:
            Dict with stock info
        """
        for attempt in range(retries):
            try:
                ticker = yf.Ticker(symbol)
                fi = ticker.fast_info

                return {
                    'symbol': symbol,
                    'name': getattr(fi, 'long_name', None) or getattr(fi, 'short_name', None) or symbol,
                    'sector': 'Unknown',  # fast_info doesn't have sector
                    'industry': 'Unknown',
                    'market_cap': getattr(fi, 'market_cap', None),
                    'currency': getattr(fi, 'currency', 'USD'),
                }
            except Exception as e:
                if '429' in str(e) or 'Too Many Requests' in str(e):
                    wait = 2 ** (attempt + 1)
                    log.warning(f"Rate limited on {symbol}, waiting {wait}s (attempt {attempt + 1}/{retries})")
                    time.sleep(wait)
                else:
                    log.warning(f"fast_info failed for {symbol}: {e}")
                    break

        # Fallback — return minimal info
        return {
            'symbol': symbol,
            'name': symbol,
            'sector': 'Unknown',
            'industry': 'Unknown',
        }

    def get_multiple_stock_info(self, symbols):
        """
        Get metadata for multiple stocks with rate limiting.

        Returns:
            List of info dicts
        """
        results = []
        for i, sym in enumerate(symbols):
            info = self.get_stock_info(sym)
            results.append(info)

            # Rate limit: sleep every 5 requests
            if (i + 1) % 5 == 0:
                time.sleep(1.5)

        return results