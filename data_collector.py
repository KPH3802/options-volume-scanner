"""
Data Collector Module
=====================
Fetches options volume data from Yahoo Finance.
Now includes Open Interest tracking for stronger signal detection.
Updated to use Russell 1000 (~1000 tickers) instead of S&P 500.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
from typing import Optional
import requests
import config
import database
import pandas_market_calendars as mcal
from tickers import get_ticker_list


def is_trading_day(check_date=None):
    """Check if a date is a valid NYSE trading day (not weekend or holiday)."""
    if check_date is None:
        check_date = datetime.now()
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(start_date=check_date.strftime('%Y-%m-%d'), 
                             end_date=check_date.strftime('%Y-%m-%d'))
    return len(schedule) > 0


def get_sp500_tickers() -> pd.DataFrame:
    """
    Fetch current S&P 500 tickers from Wikipedia.
    DEPRECATED: Use get_ticker_list() from tickers.py instead.
    Kept for backward compatibility.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        tables = pd.read_html(response.text)
        df = tables[0]

        df['Symbol'] = df['Symbol'].str.replace('.', '-', regex=False)

        print(f"Successfully fetched {len(df)} S&P 500 tickers.")
        return df

    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return pd.DataFrame()


def get_options_volume(ticker: str) -> dict:
    """
    Fetch current options volume AND open interest data for a single ticker.
    
    Open Interest represents total outstanding contracts - when combined with
    volume, it helps distinguish new positions from closing trades:
    - High volume + OI increase = New positions being opened (strong signal)
    - High volume + OI flat/decrease = Existing positions being traded/closed
    """
    result = {
        'call_volume': 0,
        'put_volume': 0,
        'call_oi': 0,
        'put_oi': 0,
        'num_contracts': 0,
        'near_term_volume': 0,
        'near_term_oi': 0,
        'success': False
    }

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options

        if not expirations:
            return result

        total_call_volume = 0
        total_put_volume = 0
        total_call_oi = 0
        total_put_oi = 0
        total_contracts = 0
        near_term_volume = 0
        near_term_oi = 0
        near_term_cutoff = datetime.now() + timedelta(days=14)

        for exp_date_str in expirations:
            try:
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                is_near_term = exp_date <= near_term_cutoff
                opt_chain = stock.option_chain(exp_date_str)

                if hasattr(opt_chain, 'calls') and not opt_chain.calls.empty:
                    calls = opt_chain.calls
                    call_vol = calls['volume'].fillna(0).sum()
                    call_oi = calls['openInterest'].fillna(0).sum()
                    total_call_volume += int(call_vol)
                    total_call_oi += int(call_oi)
                    total_contracts += len(calls)
                    if is_near_term:
                        near_term_volume += int(call_vol)
                        near_term_oi += int(call_oi)

                if hasattr(opt_chain, 'puts') and not opt_chain.puts.empty:
                    puts = opt_chain.puts
                    put_vol = puts['volume'].fillna(0).sum()
                    put_oi = puts['openInterest'].fillna(0).sum()
                    total_put_volume += int(put_vol)
                    total_put_oi += int(put_oi)
                    total_contracts += len(puts)
                    if is_near_term:
                        near_term_volume += int(put_vol)
                        near_term_oi += int(put_oi)

            except Exception:
                continue

        result['call_volume'] = total_call_volume
        result['put_volume'] = total_put_volume
        result['call_oi'] = total_call_oi
        result['put_oi'] = total_put_oi
        result['num_contracts'] = total_contracts
        result['near_term_volume'] = near_term_volume
        result['near_term_oi'] = near_term_oi
        result['success'] = True

    except Exception as e:
        print(f"Error fetching options for {ticker}: {e}")

    return result


def get_earnings_date(ticker: str) -> Optional[datetime]:
    """Fetch the next earnings date for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar

        if calendar is not None and not calendar.empty:
            if 'Earnings Date' in calendar.index:
                earnings_dates = calendar.loc['Earnings Date']
                if pd.notna(earnings_dates).any():
                    if isinstance(earnings_dates, pd.Series):
                        for date in earnings_dates:
                            if pd.notna(date):
                                return pd.to_datetime(date)
                    else:
                        return pd.to_datetime(earnings_dates)

        if hasattr(stock, 'earnings_dates') and stock.earnings_dates is not None:
            dates_df = stock.earnings_dates
            if not dates_df.empty:
                future_dates = dates_df[dates_df.index > datetime.now()]
                if not future_dates.empty:
                    return future_dates.index[0].to_pydatetime()
    except Exception:
        pass

    return None


def collect_all_options_data(tickers: list = None, progress_callback=None) -> dict:
    """Collect options volume and open interest data for all tickers."""
    database.init_database()

    if tickers is None:
        # Use Russell 1000 by default (expanded from S&P 500)
        tickers = get_ticker_list("russell1000")
        print(f"Using Russell 1000 ticker list: {len(tickers)} tickers")

    total = len(tickers)
    successful = 0
    failed = 0
    skipped = 0
    trade_date = datetime.now()

    if not is_trading_day(trade_date):
        print(f"Today is {trade_date.strftime('%A')} - market is closed.")
        print("Data collection skipped. Run this on a trading day.")
        return {
            'total': total, 'successful': 0, 'failed': 0, 'skipped': total,
            'trade_date': trade_date.strftime('%Y-%m-%d'),
            'status': 'skipped_weekend'
        }

    print(f"\nStarting data collection for {total} tickers...")
    print(f"Trade date: {trade_date.strftime('%Y-%m-%d')}")
    print("Collecting: Volume + Open Interest")
    print("-" * 50)

    for i, ticker in enumerate(tickers):
        try:
            if progress_callback:
                progress_callback(i + 1, total, ticker)
            elif (i + 1) % 50 == 0 or i == 0:
                print(f"Progress: {i + 1}/{total} ({ticker})")

            vol_data = get_options_volume(ticker)

            if vol_data['success']:
                database.save_daily_volume(
                    ticker=ticker,
                    trade_date=trade_date,
                    call_volume=vol_data['call_volume'],
                    put_volume=vol_data['put_volume'],
                    num_contracts=vol_data['num_contracts'],
                    near_term_volume=vol_data['near_term_volume'],
                    call_oi=vol_data['call_oi'],
                    put_oi=vol_data['put_oi'],
                    near_term_oi=vol_data['near_term_oi']
                )
                successful += 1

                earnings_date = get_earnings_date(ticker)
                if earnings_date:
                    database.save_earnings_date(ticker, earnings_date)
            else:
                failed += 1

            time.sleep(config.API_DELAY)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            failed += 1
            continue

    print("-" * 50)
    print(f"Collection complete!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {total}")

    return {
        'total': total, 'successful': successful, 'failed': failed,
        'skipped': skipped, 'trade_date': trade_date.strftime('%Y-%m-%d'),
        'status': 'complete'
    }


def collect_single_ticker(ticker: str) -> dict:
    """Collect and save options data for a single ticker."""
    database.init_database()
    trade_date = datetime.now()

    print(f"Collecting data for {ticker}...")
    vol_data = get_options_volume(ticker)

    if vol_data['success']:
        database.save_daily_volume(
            ticker=ticker,
            trade_date=trade_date,
            call_volume=vol_data['call_volume'],
            put_volume=vol_data['put_volume'],
            num_contracts=vol_data['num_contracts'],
            near_term_volume=vol_data['near_term_volume'],
            call_oi=vol_data['call_oi'],
            put_oi=vol_data['put_oi'],
            near_term_oi=vol_data['near_term_oi']
        )
        total_vol = vol_data['call_volume'] + vol_data['put_volume']
        total_oi = vol_data['call_oi'] + vol_data['put_oi']
        print(f"Saved: Volume={total_vol:,}, Open Interest={total_oi:,}")
    else:
        print(f"Failed to fetch data for {ticker}")

    return vol_data
