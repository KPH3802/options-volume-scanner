"""
Analyzer Module
===============
Analyzes options volume data to detect anomalies.
Now includes Open Interest analysis for stronger combined signals.
Plus Put/Call ratio and Near-term volume analysis.

Signal Types:
- COMBINED: Volume spike + OI increase (strongest - new positions being opened)
- VOLUME_ONLY: Volume spike but OI flat/down (moderate - could be closing trades)
- OI_SURGE: Large OI increase without volume spike (accumulation pattern)
- PUTCALL_EXTREME: Put/Call ratio is significantly elevated or depressed
- NEARTERM_SPIKE: Near-term (short-dated) options have unusual volume concentration
"""

from datetime import datetime, timedelta
from typing import Optional
import config
import database


# OI change thresholds
OI_INCREASE_THRESHOLD = 10.0  # % increase in OI to flag as "increasing"
OI_SURGE_THRESHOLD = 25.0     # % increase in OI to flag as standalone signal

# Put/Call ratio thresholds
PUTCALL_HIGH_THRESHOLD = 1.5   # Ratio above this = elevated put buying (bearish)
PUTCALL_LOW_THRESHOLD = 0.5    # Ratio below this = elevated call buying (bullish)
PUTCALL_EXTREME_HIGH = 2.0     # Very bearish
PUTCALL_EXTREME_LOW = 0.3      # Very bullish

# Near-term volume thresholds  
NEARTERM_RATIO_THRESHOLD = 0.6  # If near-term is >60% of total, flag it
NEARTERM_RATIO_HIGH = 0.75      # Very high near-term concentration


def calculate_adjusted_average(raw_avg: float, day_of_week: int) -> float:
    """
    Adjust average volume for day-of-week effects.
    
    If today is Friday (typically higher volume), we expect more volume,
    so we adjust the threshold upward.
    """
    adjustment_factor = config.DAY_OF_WEEK_FACTORS.get(day_of_week, 1.0)
    return raw_avg * adjustment_factor


def analyze_ticker(ticker: str, trade_date: Optional[datetime] = None) -> dict:
    """
    Analyze a single ticker for volume and OI anomalies.
    
    Returns a dictionary with:
        - ticker: The ticker symbol
        - is_anomaly: Boolean indicating if this is flagged
        - signal_type: 'combined', 'volume_only', 'oi_surge', 'putcall_extreme', 'nearterm_spike', or None
        - volume_today: Today's total volume
        - call_volume: Today's call volume
        - put_volume: Today's put volume
        - putcall_ratio: Put/Call volume ratio
        - nearterm_volume: Near-term options volume
        - nearterm_ratio: Near-term as % of total volume
        - oi_today: Today's total open interest
        - oi_change_pct: Percentage change in OI from previous day
        - averages: Dict of average volumes by period
        - std_dev: Standard deviation of 1-month volume
        - deviation_multiple: How many std devs above mean
        - percentage_above: Percentage above average
        - near_earnings: Boolean if near earnings date
        - reason: Why it was flagged (or why not)
    """
    if trade_date is None:
        trade_date = datetime.now()
    
    day_of_week = trade_date.weekday()
    
    result = {
        'ticker': ticker,
        'is_anomaly': False,
        'signal_type': None,
        'volume_today': 0,
        'call_volume': 0,
        'put_volume': 0,
        'putcall_ratio': None,
        'nearterm_volume': 0,
        'nearterm_ratio': None,
        'oi_today': 0,
        'oi_change_pct': 0,
        'averages': {},
        'std_dev': 0,
        'deviation_multiple': 0,
        'percentage_above': 0,
        'near_earnings': False,
        'reason': '',
        'flags': []
    }
    
    # Get today's volume with breakdown
    volume_data = database.get_today_volume_breakdown(ticker, trade_date)
    
    if volume_data is None:
        # Fallback to old method if breakdown not available
        volume_today = database.get_today_volume(ticker, trade_date)
        if volume_today is None:
            result['reason'] = 'No data for today'
            return result
        result['volume_today'] = volume_today
    else:
        result['volume_today'] = volume_data['total_volume']
        result['call_volume'] = volume_data['call_volume']
        result['put_volume'] = volume_data['put_volume']
        result['nearterm_volume'] = volume_data['near_term_volume']
    
    # Calculate Put/Call ratio
    if result['call_volume'] and result['call_volume'] > 0:
        result['putcall_ratio'] = result['put_volume'] / result['call_volume']
    
    # Calculate near-term ratio
    if result['volume_today'] and result['volume_today'] > 0 and result['nearterm_volume']:
        result['nearterm_ratio'] = result['nearterm_volume'] / result['volume_today']
    
    # Get today's OI
    oi_today = database.get_today_oi(ticker, trade_date)
    result['oi_today'] = oi_today or 0
    
    # Check if near earnings
    result['near_earnings'] = database.is_near_earnings(ticker, trade_date)
    
    # Calculate averages for different periods
    periods = {
        '1_week': 5,      # ~5 trading days
        '1_month': 21,    # ~21 trading days
        '3_month': 63,    # ~63 trading days
        '6_month': 126    # ~126 trading days
    }
    
    for period_name, days in periods.items():
        stats = database.get_volume_stats(ticker, days, trade_date)
        
        min_days_required = config.MIN_DAYS_FOR_AVERAGE.get(period_name, 5)
        
        if stats['count'] >= min_days_required:
            # Apply day-of-week adjustment
            adjusted_avg = calculate_adjusted_average(stats['avg'], day_of_week)
            result['averages'][period_name] = {
                'raw_avg': stats['avg'],
                'adjusted_avg': adjusted_avg,
                'std_dev': stats['std_dev'],
                'data_points': stats['count']
            }
        else:
            result['averages'][period_name] = {
                'raw_avg': None,
                'adjusted_avg': None,
                'std_dev': None,
                'data_points': stats['count'],
                'note': f'Insufficient data ({stats["count"]}/{min_days_required} days)'
            }
    
    # Calculate OI change from previous day
    oi_stats = database.get_oi_stats(ticker, 5, trade_date)  # Get recent OI data
    if oi_stats['prev_oi'] and oi_stats['prev_oi'] > 0 and oi_today:
        oi_change_pct = ((oi_today - oi_stats['prev_oi']) / oi_stats['prev_oi']) * 100
        result['oi_change_pct'] = oi_change_pct
    
    # Use 1-month average as primary comparison (most stable)
    if result['averages'].get('1_month', {}).get('adjusted_avg') is not None:
        avg_1month = result['averages']['1_month']['adjusted_avg']
        std_dev = result['averages']['1_month']['std_dev']
        
        result['std_dev'] = std_dev
        
        # Skip if average volume is too low (illiquid options)
        if avg_1month < config.MIN_AVERAGE_VOLUME:
            result['reason'] = f'Low liquidity (avg volume: {avg_1month:.0f})'
            return result
        
        # Calculate deviation metrics
        if std_dev > 0:
            deviation_multiple = (result['volume_today'] - avg_1month) / std_dev
            result['deviation_multiple'] = deviation_multiple
        else:
            result['deviation_multiple'] = 0
        
        if avg_1month > 0:
            percentage_above = ((result['volume_today'] - avg_1month) / avg_1month) * 100
            result['percentage_above'] = percentage_above
        
        # Check anomaly conditions
        flags = []
        volume_anomaly = False
        oi_increasing = False
        oi_surge = False
        putcall_extreme = False
        nearterm_high = False
        
        # Condition 1: Standard deviation threshold for volume
        if result['deviation_multiple'] >= config.STD_DEV_THRESHOLD:
            flags.append(f"{result['deviation_multiple']:.1f}σ volume")
            volume_anomaly = True
        
        # Condition 2: Percentage threshold for volume
        if result['percentage_above'] >= config.PERCENTAGE_THRESHOLD:
            flags.append(f"+{result['percentage_above']:.0f}% volume")
            volume_anomaly = True
        
        # Condition 3: OI change analysis
        if result['oi_change_pct'] >= OI_INCREASE_THRESHOLD:
            flags.append(f"+{result['oi_change_pct']:.1f}% OI")
            oi_increasing = True
        
        if result['oi_change_pct'] >= OI_SURGE_THRESHOLD:
            oi_surge = True
        
        # Condition 4: Put/Call ratio extreme
        if result['putcall_ratio'] is not None:
            if result['putcall_ratio'] >= PUTCALL_EXTREME_HIGH:
                flags.append(f"P/C {result['putcall_ratio']:.2f} (very bearish)")
                putcall_extreme = True
            elif result['putcall_ratio'] >= PUTCALL_HIGH_THRESHOLD:
                flags.append(f"P/C {result['putcall_ratio']:.2f} (bearish)")
                putcall_extreme = True
            elif result['putcall_ratio'] <= PUTCALL_EXTREME_LOW:
                flags.append(f"P/C {result['putcall_ratio']:.2f} (very bullish)")
                putcall_extreme = True
            elif result['putcall_ratio'] <= PUTCALL_LOW_THRESHOLD:
                flags.append(f"P/C {result['putcall_ratio']:.2f} (bullish)")
                putcall_extreme = True
        
        # Condition 5: Near-term concentration
        if result['nearterm_ratio'] is not None:
            if result['nearterm_ratio'] >= NEARTERM_RATIO_HIGH:
                flags.append(f"{result['nearterm_ratio']*100:.0f}% near-term (speculative)")
                nearterm_high = True
            elif result['nearterm_ratio'] >= NEARTERM_RATIO_THRESHOLD:
                flags.append(f"{result['nearterm_ratio']*100:.0f}% near-term")
                nearterm_high = True
        
        # Determine signal type and whether to flag
        # Priority order: combined > volume_only > oi_surge > putcall_extreme > nearterm_spike
        
        if volume_anomaly and oi_increasing:
            # STRONGEST SIGNAL: Volume spike + OI increase = new positions
            result['is_anomaly'] = True
            result['signal_type'] = 'combined'
            result['flags'] = flags
            prefix = "🔴 COMBINED SIGNAL" if not result['near_earnings'] else "COMBINED (near earnings)"
            result['reason'] = f"{prefix}: {', '.join(flags)}"
            
        elif volume_anomaly:
            # MODERATE SIGNAL: Volume spike without OI increase
            result['is_anomaly'] = True
            result['signal_type'] = 'volume_only'
            result['flags'] = flags
            if result['oi_change_pct'] < 0:
                flags.append(f"{result['oi_change_pct']:.1f}% OI (closing)")
            prefix = "🟡 VOLUME ONLY" if not result['near_earnings'] else "VOLUME (near earnings)"
            result['reason'] = f"{prefix}: {', '.join(flags)}"
            
        elif oi_surge and not volume_anomaly:
            # ACCUMULATION PATTERN: OI building without volume spike
            result['is_anomaly'] = True
            result['signal_type'] = 'oi_surge'
            result['flags'] = flags
            prefix = "🟠 OI SURGE" if not result['near_earnings'] else "OI SURGE (near earnings)"
            result['reason'] = f"{prefix}: {', '.join(flags)}"
        
        elif putcall_extreme and result['volume_today'] > avg_1month:
            # PUT/CALL EXTREME: Unusual ratio with above-average volume
            result['is_anomaly'] = True
            result['signal_type'] = 'putcall_extreme'
            result['flags'] = flags
            prefix = "🔵 PUT/CALL EXTREME" if not result['near_earnings'] else "P/C EXTREME (near earnings)"
            result['reason'] = f"{prefix}: {', '.join(flags)}"
        
        elif nearterm_high and result['volume_today'] > avg_1month:
            # NEAR-TERM SPIKE: Short-dated options concentrated with elevated volume
            result['is_anomaly'] = True
            result['signal_type'] = 'nearterm_spike'
            result['flags'] = flags
            prefix = "⚡ NEAR-TERM SPIKE" if not result['near_earnings'] else "NEAR-TERM (near earnings)"
            result['reason'] = f"{prefix}: {', '.join(flags)}"
            
        else:
            if flags:
                result['reason'] = f"Minor signals: {', '.join(flags)}"
            else:
                result['reason'] = 'Within normal range'
    else:
        result['reason'] = 'Insufficient historical data for analysis'
    
    return result


def analyze_all_tickers(tickers: list = None, 
                        trade_date: Optional[datetime] = None,
                        progress_callback=None) -> dict:
    """
    Analyze all tickers and return anomalies.
    
    Returns:
        Dictionary with:
            - anomalies: List of flagged tickers with details (sorted by signal strength)
            - earnings_related: List of flagged tickers near earnings
            - summary: Overall statistics
    """
    if trade_date is None:
        trade_date = datetime.now()
    
    # If no tickers provided, get from today's data
    if tickers is None:
        from data_collector import get_sp500_tickers
        sp500_df = get_sp500_tickers()
        tickers = sp500_df['Symbol'].tolist()
    
    anomalies = []
    earnings_related = []
    analyzed = 0
    skipped = 0
    total = len(tickers)
    
    # Check if we have OI data
    has_oi = database.has_oi_data()
    
    print(f"\nAnalyzing {total} tickers for anomalies...")
    print(f"Analysis date: {trade_date.strftime('%Y-%m-%d')}")
    print(f"OI data available: {'Yes' if has_oi else 'No (will be collected today)'}")
    print("-" * 50)
    
    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i + 1, total, ticker)
        elif (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{total}")
        
        result = analyze_ticker(ticker, trade_date)
        
        if result['volume_today'] == 0 and 'No data' in result['reason']:
            skipped += 1
            continue
        
        analyzed += 1
        
        if result['is_anomaly']:
            if result['near_earnings']:
                earnings_related.append(result)
            else:
                anomalies.append(result)
    
    # Sort anomalies by signal strength:
    # 1. Combined signals first (strongest)
    # 2. Then by deviation multiple within each type
    def sort_key(x):
        type_priority = {
            'combined': 0, 
            'volume_only': 1, 
            'oi_surge': 2,
            'putcall_extreme': 3,
            'nearterm_spike': 4
        }
        return (type_priority.get(x['signal_type'], 99), -x['deviation_multiple'])
    
    anomalies.sort(key=sort_key)
    earnings_related.sort(key=sort_key)
    
    # Save anomalies to database
    for anomaly in anomalies + earnings_related:
        database.save_anomaly(
            ticker=anomaly['ticker'],
            detected_date=trade_date,
            volume_today=anomaly['volume_today'],
            avg_1week=anomaly['averages'].get('1_week', {}).get('adjusted_avg', 0) or 0,
            avg_1month=anomaly['averages'].get('1_month', {}).get('adjusted_avg', 0) or 0,
            avg_3month=anomaly['averages'].get('3_month', {}).get('adjusted_avg', 0) or 0,
            std_dev=anomaly['std_dev'],
            deviation_multiple=anomaly['deviation_multiple'],
            percentage_above=anomaly['percentage_above'],
            near_earnings=anomaly['near_earnings'],
            notes=anomaly['reason'],
            oi_today=anomaly['oi_today'],
            oi_change_pct=anomaly['oi_change_pct'],
            signal_type=anomaly['signal_type'] or 'unknown'
        )
    
    # Count by signal type
    combined_count = len([a for a in anomalies if a['signal_type'] == 'combined'])
    volume_only_count = len([a for a in anomalies if a['signal_type'] == 'volume_only'])
    oi_surge_count = len([a for a in anomalies if a['signal_type'] == 'oi_surge'])
    putcall_count = len([a for a in anomalies if a['signal_type'] == 'putcall_extreme'])
    nearterm_count = len([a for a in anomalies if a['signal_type'] == 'nearterm_spike'])
    
    print("-" * 50)
    print(f"Analysis complete!")
    print(f"  Analyzed: {analyzed}")
    print(f"  Skipped (no data): {skipped}")
    print(f"  Anomalies found: {len(anomalies)}")
    if has_oi:
        print(f"    - Combined (Volume+OI): {combined_count}")
        print(f"    - Volume only: {volume_only_count}")
        print(f"    - OI surge: {oi_surge_count}")
        print(f"    - Put/Call extreme: {putcall_count}")
        print(f"    - Near-term spike: {nearterm_count}")
    print(f"  Earnings-related: {len(earnings_related)}")
    
    return {
        'anomalies': anomalies,
        'earnings_related': earnings_related,
        'summary': {
            'total_tickers': total,
            'analyzed': analyzed,
            'skipped': skipped,
            'anomalies_count': len(anomalies),
            'combined_count': combined_count,
            'volume_only_count': volume_only_count,
            'oi_surge_count': oi_surge_count,
            'putcall_count': putcall_count,
            'nearterm_count': nearterm_count,
            'earnings_related_count': len(earnings_related),
            'trade_date': trade_date.strftime('%Y-%m-%d'),
            'has_oi_data': has_oi
        }
    }


def get_database_status() -> dict:
    """
    Get current status of the database for reporting.
    """
    collection_dates = database.get_collection_dates()
    
    status = {
        'total_days_collected': len(collection_dates),
        'first_date': collection_dates[-1] if collection_dates else None,
        'last_date': collection_dates[0] if collection_dates else None,
        'collection_dates': collection_dates[:10],  # Last 10 dates
        'has_oi_data': database.has_oi_data()
    }
    
    if collection_dates:
        status['tickers_last_date'] = database.get_ticker_count_for_date(collection_dates[0])
    
    return status


def format_anomaly_report(analysis_results: dict) -> str:
    """
    Format analysis results into a readable text report.
    """
    # Handle baseline mode - no 'summary' key in this case
    if analysis_results.get('baseline_mode'):
        days = analysis_results.get('days_collected', 0)
        required = analysis_results.get('days_required', 30)
        has_oi = analysis_results.get('has_oi_data', False)
        return f"""Baseline collection in progress: {days}/{required} days
OI tracking: {'Active' if has_oi else 'Starting'}
Anomaly detection will begin once baseline is complete."""

    report_lines = []
    summary = analysis_results['summary']
    
    report_lines.append("=" * 60)
    report_lines.append("OPTIONS VOLUME ANOMALY REPORT")
    report_lines.append(f"Date: {summary['trade_date']}")
    report_lines.append("=" * 60)
    report_lines.append("")
    
    # Summary stats
    report_lines.append("SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Tickers analyzed: {summary['analyzed']}")
    report_lines.append(f"Anomalies detected: {summary['anomalies_count']}")
    if summary.get('has_oi_data'):
        report_lines.append(f"  - Combined (Vol+OI): {summary['combined_count']}")
        report_lines.append(f"  - Volume only: {summary['volume_only_count']}")
        report_lines.append(f"  - OI surge: {summary['oi_surge_count']}")
        report_lines.append(f"  - Put/Call extreme: {summary.get('putcall_count', 0)}")
        report_lines.append(f"  - Near-term spike: {summary.get('nearterm_count', 0)}")
    report_lines.append(f"Earnings-related (excluded): {summary['earnings_related_count']}")
    report_lines.append("")
    
    # Database status
    db_status = get_database_status()
    report_lines.append("DATABASE STATUS")
    report_lines.append("-" * 40)
    report_lines.append(f"Days of data collected: {db_status['total_days_collected']}")
    if db_status['first_date']:
        report_lines.append(f"Date range: {db_status['first_date']} to {db_status['last_date']}")
    report_lines.append(f"Open Interest tracking: {'Active' if db_status['has_oi_data'] else 'Starting today'}")
    report_lines.append("")
    
    # Anomalies (non-earnings)
    anomalies = analysis_results['anomalies']
    if anomalies:
        report_lines.append("🚨 ANOMALIES DETECTED")
        report_lines.append("-" * 40)
        
        # Group by signal type
        combined = [a for a in anomalies if a['signal_type'] == 'combined']
        volume_only = [a for a in anomalies if a['signal_type'] == 'volume_only']
        oi_surge = [a for a in anomalies if a['signal_type'] == 'oi_surge']
        putcall = [a for a in anomalies if a['signal_type'] == 'putcall_extreme']
        nearterm = [a for a in anomalies if a['signal_type'] == 'nearterm_spike']
        
        if combined:
            report_lines.append("\n🔴 COMBINED SIGNALS (Strongest - New Positions)")
            for a in combined[:10]:
                report_lines.append(f"\n  {a['ticker']}")
                report_lines.append(f"    Volume: {a['volume_today']:,} ({a['deviation_multiple']:.1f}σ, +{a['percentage_above']:.0f}%)")
                if a['oi_today']:
                    report_lines.append(f"    Open Interest: {a['oi_today']:,} ({a['oi_change_pct']:+.1f}%)")
                if a.get('putcall_ratio'):
                    report_lines.append(f"    Put/Call Ratio: {a['putcall_ratio']:.2f}")
                report_lines.append(f"    Signal: {', '.join(a['flags'])}")
        
        if volume_only:
            report_lines.append("\n🟡 VOLUME ONLY SIGNALS")
            for a in volume_only[:10]:
                report_lines.append(f"\n  {a['ticker']}")
                report_lines.append(f"    Volume: {a['volume_today']:,} ({a['deviation_multiple']:.1f}σ, +{a['percentage_above']:.0f}%)")
                if a['oi_today']:
                    report_lines.append(f"    Open Interest: {a['oi_today']:,} ({a['oi_change_pct']:+.1f}%)")
                if a.get('putcall_ratio'):
                    report_lines.append(f"    Put/Call Ratio: {a['putcall_ratio']:.2f}")
        
        if oi_surge:
            report_lines.append("\n🟠 OI SURGE (Accumulation Pattern)")
            for a in oi_surge[:5]:
                report_lines.append(f"\n  {a['ticker']}")
                report_lines.append(f"    Volume: {a['volume_today']:,}")
                report_lines.append(f"    Open Interest: {a['oi_today']:,} ({a['oi_change_pct']:+.1f}%)")
        
        if putcall:
            report_lines.append("\n🔵 PUT/CALL EXTREME")
            for a in putcall[:5]:
                report_lines.append(f"\n  {a['ticker']}")
                report_lines.append(f"    Volume: {a['volume_today']:,}")
                report_lines.append(f"    Put/Call Ratio: {a['putcall_ratio']:.2f}")
                sentiment = "BEARISH" if a['putcall_ratio'] > 1 else "BULLISH"
                report_lines.append(f"    Sentiment: {sentiment}")
        
        if nearterm:
            report_lines.append("\n⚡ NEAR-TERM SPIKE (Short-dated focus)")
            for a in nearterm[:5]:
                report_lines.append(f"\n  {a['ticker']}")
                report_lines.append(f"    Volume: {a['volume_today']:,}")
                report_lines.append(f"    Near-term: {a['nearterm_ratio']*100:.0f}% of total")
    else:
        report_lines.append("✅ NO ANOMALIES DETECTED")
        report_lines.append("-" * 40)
        report_lines.append("All tickers within normal volume ranges.")
    
    report_lines.append("")
    
    # Earnings-related (for reference)
    earnings = analysis_results['earnings_related']
    if earnings:
        report_lines.append("📅 EARNINGS-RELATED (For Reference)")
        report_lines.append("-" * 40)
        report_lines.append("These tickers have unusual volume but are near earnings dates.")
        report_lines.append("High volume is expected and likely not suspicious.")
        report_lines.append("")
        
        for e in earnings[:10]:  # Top 10
            report_lines.append(f"  {e['ticker']}: {e['volume_today']:,} vol "
                              f"({e['percentage_above']:.0f}% above avg)")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("End of Report")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    # Test analyzer
    print("Testing analyzer...")
    
    # Check database status first
    status = get_database_status()
    print(f"\nDatabase status:")
    print(f"  Days collected: {status['total_days_collected']}")
    print(f"  OI data available: {status['has_oi_data']}")
    
    if status['total_days_collected'] == 0:
        print("\nNo data in database. Run data_collector.py first.")
    else:
        print(f"\nAnalyzing single ticker (AAPL):")
        result = analyze_ticker("AAPL")
        print(f"  Volume today: {result['volume_today']:,}")
        print(f"  Call volume: {result.get('call_volume', 0):,}")
        print(f"  Put volume: {result.get('put_volume', 0):,}")
        print(f"  Put/Call ratio: {result.get('putcall_ratio') or 'N/A'}")
        nt_display = f"{result.get('nearterm_ratio')*100:.0f}%" if result.get('nearterm_ratio') else "N/A"
        print(f"  Near-term ratio: {nt_display}")
        print(f"  OI today: {result['oi_today']:,}")
        print(f"  OI change: {result['oi_change_pct']:+.1f}%")
        print(f"  Is anomaly: {result['is_anomaly']}")
        print(f"  Signal type: {result['signal_type']}")
        print(f"  Reason: {result['reason']}")
    
    print("\nAnalyzer test complete.")
