"""
Database Module
===============
Handles all SQLite database operations for the options scanner.
Now includes Open Interest tracking and Put/Call ratio support.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import config


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_database():
    """
    Initialize the database with required tables.
    Safe to call multiple times - uses IF NOT EXISTS.
    Also handles migration to add OI columns to existing databases.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main table for daily options volume data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_options_volume (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            trade_date DATE NOT NULL,
            day_of_week INTEGER NOT NULL,  -- 0=Monday, 6=Sunday
            total_call_volume INTEGER DEFAULT 0,
            total_put_volume INTEGER DEFAULT 0,
            total_volume INTEGER DEFAULT 0,
            num_contracts INTEGER DEFAULT 0,  -- Number of option contracts available
            near_term_volume INTEGER DEFAULT 0,  -- Volume in options expiring within 2 weeks
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, trade_date)
        )
    """)
    
    # Migration: Add Open Interest columns if they don't exist
    # This preserves existing data while adding new functionality
    try:
        cursor.execute("ALTER TABLE daily_options_volume ADD COLUMN total_call_oi INTEGER DEFAULT 0")
        print("Added column: total_call_oi")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE daily_options_volume ADD COLUMN total_put_oi INTEGER DEFAULT 0")
        print("Added column: total_put_oi")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE daily_options_volume ADD COLUMN total_oi INTEGER DEFAULT 0")
        print("Added column: total_oi")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE daily_options_volume ADD COLUMN near_term_oi INTEGER DEFAULT 0")
        print("Added column: near_term_oi")
    except sqlite3.OperationalError:
        pass
    
    # Index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ticker_date 
        ON daily_options_volume(ticker, trade_date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_trade_date 
        ON daily_options_volume(trade_date)
    """)
    
    # Table for earnings calendar data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS earnings_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            earnings_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, earnings_date)
        )
    """)
    
    # Table to track S&P 500 tickers (so we can track changes over time)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sp500_tickers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            sector TEXT,
            date_added DATE NOT NULL,
            date_removed DATE,
            is_active BOOLEAN DEFAULT 1,
            UNIQUE(ticker, date_added)
        )
    """)
    
    # Table for detected anomalies (for record keeping)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            detected_date DATE NOT NULL,
            volume_today INTEGER,
            avg_volume_1week REAL,
            avg_volume_1month REAL,
            avg_volume_3month REAL,
            std_dev_1month REAL,
            deviation_multiple REAL,  -- How many std devs above mean
            percentage_above_avg REAL,
            near_earnings BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migration: Add OI columns to anomalies table
    try:
        cursor.execute("ALTER TABLE anomalies ADD COLUMN oi_today INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE anomalies ADD COLUMN oi_change_pct REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE anomalies ADD COLUMN signal_type TEXT DEFAULT 'volume_only'")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def save_daily_volume(ticker: str, trade_date: datetime, 
                      call_volume: int, put_volume: int,
                      num_contracts: int, near_term_volume: int,
                      call_oi: int = 0, put_oi: int = 0, near_term_oi: int = 0):
    """
    Save daily options volume and open interest data for a ticker.
    Uses INSERT OR REPLACE to handle re-runs on the same day.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    total_volume = call_volume + put_volume
    total_oi = call_oi + put_oi
    day_of_week = trade_date.weekday()
    
    cursor.execute("""
        INSERT OR REPLACE INTO daily_options_volume 
        (ticker, trade_date, day_of_week, total_call_volume, total_put_volume, 
         total_volume, num_contracts, near_term_volume,
         total_call_oi, total_put_oi, total_oi, near_term_oi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, trade_date.strftime('%Y-%m-%d'), day_of_week,
          call_volume, put_volume, total_volume, num_contracts, near_term_volume,
          call_oi, put_oi, total_oi, near_term_oi))
    
    conn.commit()
    conn.close()


def get_historical_volumes(ticker: str, days_back: int, 
                           end_date: Optional[datetime] = None) -> list:
    """
    Get historical volume and OI data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        days_back: Number of trading days to look back
        end_date: End date for the query (defaults to today)
    
    Returns:
        List of dictionaries with volume and OI data
    """
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back * 1.5)  # Buffer for weekends
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ticker, trade_date, day_of_week, total_call_volume, 
               total_put_volume, total_volume, near_term_volume,
               total_call_oi, total_put_oi, total_oi, near_term_oi
        FROM daily_options_volume
        WHERE ticker = ? 
          AND trade_date BETWEEN ? AND ?
        ORDER BY trade_date DESC
        LIMIT ?
    """, (ticker, start_date.strftime('%Y-%m-%d'), 
          end_date.strftime('%Y-%m-%d'), days_back))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_volume_stats(ticker: str, days_back: int, 
                     end_date: Optional[datetime] = None) -> dict:
    """
    Calculate volume statistics for a ticker over a period.
    
    Returns dict with: count, avg, std_dev, min, max
    """
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back * 1.5)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as count,
            AVG(total_volume) as avg,
            AVG(total_volume * total_volume) - AVG(total_volume) * AVG(total_volume) as variance,
            MIN(total_volume) as min,
            MAX(total_volume) as max
        FROM daily_options_volume
        WHERE ticker = ? 
          AND trade_date BETWEEN ? AND ?
          AND trade_date < ?
    """, (ticker, start_date.strftime('%Y-%m-%d'), 
          end_date.strftime('%Y-%m-%d'),
          end_date.strftime('%Y-%m-%d')))  # Exclude today from historical calc
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row['count'] > 0:
        variance = row['variance'] or 0
        std_dev = variance ** 0.5 if variance > 0 else 0
        return {
            'count': row['count'],
            'avg': row['avg'] or 0,
            'std_dev': std_dev,
            'min': row['min'] or 0,
            'max': row['max'] or 0
        }
    return {'count': 0, 'avg': 0, 'std_dev': 0, 'min': 0, 'max': 0}


def get_oi_stats(ticker: str, days_back: int,
                 end_date: Optional[datetime] = None) -> dict:
    """
    Calculate open interest statistics for a ticker over a period.
    
    Returns dict with: count, avg, std_dev, min, max, prev_oi
    """
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back * 1.5)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get aggregate stats
    cursor.execute("""
        SELECT 
            COUNT(*) as count,
            AVG(total_oi) as avg,
            AVG(total_oi * total_oi) - AVG(total_oi) * AVG(total_oi) as variance,
            MIN(total_oi) as min,
            MAX(total_oi) as max
        FROM daily_options_volume
        WHERE ticker = ? 
          AND trade_date BETWEEN ? AND ?
          AND trade_date < ?
          AND total_oi > 0
    """, (ticker, start_date.strftime('%Y-%m-%d'), 
          end_date.strftime('%Y-%m-%d'),
          end_date.strftime('%Y-%m-%d')))
    
    row = cursor.fetchone()
    
    # Get previous day's OI for change calculation
    cursor.execute("""
        SELECT total_oi
        FROM daily_options_volume
        WHERE ticker = ? 
          AND trade_date < ?
          AND total_oi > 0
        ORDER BY trade_date DESC
        LIMIT 1
    """, (ticker, end_date.strftime('%Y-%m-%d')))
    
    prev_row = cursor.fetchone()
    conn.close()
    
    result = {'count': 0, 'avg': 0, 'std_dev': 0, 'min': 0, 'max': 0, 'prev_oi': 0}
    
    if row and row['count'] > 0:
        variance = row['variance'] or 0
        std_dev = variance ** 0.5 if variance > 0 else 0
        result = {
            'count': row['count'],
            'avg': row['avg'] or 0,
            'std_dev': std_dev,
            'min': row['min'] or 0,
            'max': row['max'] or 0,
            'prev_oi': prev_row['total_oi'] if prev_row else 0
        }
    
    return result


def get_today_volume(ticker: str, trade_date: Optional[datetime] = None) -> Optional[int]:
    """Get today's total volume for a ticker."""
    if trade_date is None:
        trade_date = datetime.now()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_volume 
        FROM daily_options_volume
        WHERE ticker = ? AND trade_date = ?
    """, (ticker, trade_date.strftime('%Y-%m-%d')))
    
    row = cursor.fetchone()
    conn.close()
    
    return row['total_volume'] if row else None


def get_today_volume_breakdown(ticker: str, trade_date: Optional[datetime] = None) -> Optional[dict]:
    """
    Get today's volume breakdown (calls, puts, near-term) for a ticker.
    
    Returns dict with: total_volume, call_volume, put_volume, near_term_volume
    """
    if trade_date is None:
        trade_date = datetime.now()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_volume, total_call_volume, total_put_volume, near_term_volume
        FROM daily_options_volume
        WHERE ticker = ? AND trade_date = ?
    """, (ticker, trade_date.strftime('%Y-%m-%d')))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'total_volume': row['total_volume'] or 0,
            'call_volume': row['total_call_volume'] or 0,
            'put_volume': row['total_put_volume'] or 0,
            'near_term_volume': row['near_term_volume'] or 0
        }
    return None


def get_today_oi(ticker: str, trade_date: Optional[datetime] = None) -> Optional[int]:
    """Get today's total open interest for a ticker."""
    if trade_date is None:
        trade_date = datetime.now()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_oi 
        FROM daily_options_volume
        WHERE ticker = ? AND trade_date = ?
    """, (ticker, trade_date.strftime('%Y-%m-%d')))
    
    row = cursor.fetchone()
    conn.close()
    
    return row['total_oi'] if row else None


def get_putcall_stats(ticker: str, days_back: int,
                      end_date: Optional[datetime] = None) -> dict:
    """
    Calculate historical put/call ratio statistics for a ticker.
    
    Returns dict with: count, avg_ratio, std_dev, min_ratio, max_ratio
    """
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back * 1.5)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get historical put/call ratios
    cursor.execute("""
        SELECT total_put_volume, total_call_volume
        FROM daily_options_volume
        WHERE ticker = ? 
          AND trade_date BETWEEN ? AND ?
          AND trade_date < ?
          AND total_call_volume > 0
    """, (ticker, start_date.strftime('%Y-%m-%d'), 
          end_date.strftime('%Y-%m-%d'),
          end_date.strftime('%Y-%m-%d')))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {'count': 0, 'avg_ratio': 1.0, 'std_dev': 0, 'min_ratio': 0, 'max_ratio': 0}
    
    ratios = []
    for row in rows:
        if row['total_call_volume'] > 0:
            ratio = row['total_put_volume'] / row['total_call_volume']
            ratios.append(ratio)
    
    if not ratios:
        return {'count': 0, 'avg_ratio': 1.0, 'std_dev': 0, 'min_ratio': 0, 'max_ratio': 0}
    
    avg_ratio = sum(ratios) / len(ratios)
    variance = sum((r - avg_ratio) ** 2 for r in ratios) / len(ratios) if len(ratios) > 1 else 0
    std_dev = variance ** 0.5
    
    return {
        'count': len(ratios),
        'avg_ratio': avg_ratio,
        'std_dev': std_dev,
        'min_ratio': min(ratios),
        'max_ratio': max(ratios)
    }


def get_tickers_for_date(trade_date: Optional[datetime] = None) -> list:
    """Get list of all tickers that have data for a specific date."""
    if trade_date is None:
        trade_date = datetime.now()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT ticker
        FROM daily_options_volume
        WHERE trade_date = ?
        ORDER BY ticker
    """, (trade_date.strftime('%Y-%m-%d'),))
    
    results = [row['ticker'] for row in cursor.fetchall()]
    conn.close()
    return results


def save_earnings_date(ticker: str, earnings_date: datetime):
    """Save an earnings date for a ticker."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO earnings_calendar (ticker, earnings_date)
        VALUES (?, ?)
    """, (ticker, earnings_date.strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()


def is_near_earnings(ticker: str, check_date: Optional[datetime] = None) -> bool:
    """
    Check if a date is near an earnings announcement.
    Uses the exclusion window defined in config.
    """
    if check_date is None:
        check_date = datetime.now()
    
    start_window = check_date - timedelta(days=config.EARNINGS_EXCLUSION_DAYS_BEFORE)
    end_window = check_date + timedelta(days=config.EARNINGS_EXCLUSION_DAYS_AFTER)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM earnings_calendar
        WHERE ticker = ? 
          AND earnings_date BETWEEN ? AND ?
    """, (ticker, start_window.strftime('%Y-%m-%d'), 
          end_window.strftime('%Y-%m-%d')))
    
    row = cursor.fetchone()
    conn.close()
    
    return row['count'] > 0 if row else False


def save_anomaly(ticker: str, detected_date: datetime, volume_today: int,
                 avg_1week: float, avg_1month: float, avg_3month: float,
                 std_dev: float, deviation_multiple: float, 
                 percentage_above: float, near_earnings: bool,
                 notes: str = "", oi_today: int = 0, oi_change_pct: float = 0,
                 signal_type: str = "volume_only"):
    """Save a detected anomaly to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO anomalies 
        (ticker, detected_date, volume_today, avg_volume_1week, avg_volume_1month,
         avg_volume_3month, std_dev_1month, deviation_multiple, percentage_above_avg,
         near_earnings, notes, oi_today, oi_change_pct, signal_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, detected_date.strftime('%Y-%m-%d'), volume_today,
          avg_1week, avg_1month, avg_3month, std_dev, deviation_multiple,
          percentage_above, near_earnings, notes, oi_today, oi_change_pct, signal_type))
    
    conn.commit()
    conn.close()


def get_collection_dates() -> list:
    """Get list of all dates we have data for."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT trade_date 
        FROM daily_options_volume 
        ORDER BY trade_date DESC
    """)
    
    results = [row['trade_date'] for row in cursor.fetchall()]
    conn.close()
    return results


def get_ticker_count_for_date(trade_date: str) -> int:
    """Get count of tickers collected for a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(DISTINCT ticker) as count
        FROM daily_options_volume 
        WHERE trade_date = ?
    """, (trade_date,))
    
    row = cursor.fetchone()
    conn.close()
    return row['count'] if row else 0


def has_oi_data() -> bool:
    """Check if we have any OI data collected yet."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM daily_options_volume
        WHERE total_oi > 0
    """)
    
    row = cursor.fetchone()
    conn.close()
    return row['count'] > 0 if row else False


if __name__ == "__main__":
    # Test database initialization
    init_database()
    print("\nChecking for OI data...")
    if has_oi_data():
        print("OI data exists in database.")
    else:
        print("No OI data yet - will be collected on next run.")
    print("\nDatabase module test complete.")
