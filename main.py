#!/usr/bin/env python3
"""
Options Volume Scanner - Main Script
====================================
Run this script daily (after market close) to:
1. Collect options volume data for S&P 500 stocks
2. Analyze for anomalies
3. Send email report

Usage:
    python main.py              # Run full pipeline
    python main.py --collect    # Only collect data
    python main.py --analyze    # Only analyze (skip collection)
    python main.py --test-email # Send test email
    python main.py --status     # Show database status
"""

import sys
import argparse
from datetime import datetime, timezone
import time

import config
import database
import data_collector
import analyzer
import emailer


def run_collection():
    """Run the data collection phase."""
    print("\n" + "=" * 60)
    print("PHASE 1: DATA COLLECTION")
    print("=" * 60)

    start_time = time.time()
    results = data_collector.collect_all_options_data()
    elapsed = time.time() - start_time

    print(f"\nCollection completed in {elapsed/60:.1f} minutes")
    return results


def run_analysis():
    """Run the analysis phase."""
    print("\n" + "=" * 60)
    print("PHASE 2: ANOMALY ANALYSIS")
    print("=" * 60)

    # Check if we have enough data
    db_status = analyzer.get_database_status()

    days_collected = db_status['total_days_collected']
    
    # Check if we have enough baseline data
    if days_collected < config.MIN_BASELINE_DAYS:
        print(f"\n📊 Baseline collection in progress: {days_collected}/{config.MIN_BASELINE_DAYS} days")
        print("    Anomaly detection requires sufficient historical data.")
        print("    A status email will be sent instead of anomaly alerts.")
        return {
            'baseline_mode': True,
            'days_collected': days_collected,
            'days_required': config.MIN_BASELINE_DAYS,
            'anomalies': []
        }

    results = analyzer.analyze_all_tickers()
    results['baseline_mode'] = False
    return results


def run_email_report(analysis_results: dict):
    """Send the email report."""
    print("\n" + "=" * 60)
    print("PHASE 3: EMAIL REPORT")
    print("=" * 60)

    # Check if email is configured
    if "your_email" in config.EMAIL_SENDER or "xxxx" in config.EMAIL_PASSWORD:
        print("\n⚠️  Email not configured - skipping email report.")
        print("To enable email reports, edit config.py with your Gmail credentials.")
        print("\nReport preview:")
        print("-" * 40)
        print(analyzer.format_anomaly_report(analysis_results))
        return False

    success = emailer.send_daily_report(analysis_results)
    return success


def show_status():
    """Show current database status."""
    print("\n" + "=" * 60)
    print("DATABASE STATUS")
    print("=" * 60)

    database.init_database()
    status = analyzer.get_database_status()

    print(f"\nDays of data collected: {status['total_days_collected']}")

    if status['total_days_collected'] > 0:
        print(f"Date range: {status['first_date']} to {status['last_date']}")
        print(f"Tickers in last collection: {status.get('tickers_last_date', 'N/A')}")

        print("\nRecent collection dates:")
        for date in status['collection_dates'][:5]:
            count = database.get_ticker_count_for_date(date)
            print(f"  {date}: {count} tickers")
    else:
        print("\nNo data collected yet. Run with --collect to start.")

    # Check analysis readiness
    print("\nAnalysis readiness:")
    min_days = config.MIN_DAYS_FOR_AVERAGE
    for period, required in min_days.items():
        status_icon = "✅" if status['total_days_collected'] >= required else "⏳"
        print(f"  {period}: {status_icon} ({status['total_days_collected']}/{required} days)")


def main():
    """Main entry point."""
    # Skip weekends - markets closed
    if datetime.now(timezone.utc).weekday() >= 5:  # 5=Saturday, 6=Sunday
        print("Weekend - skipping scan")
        return 0

    parser = argparse.ArgumentParser(
        description="Options Volume Scanner - Detect unusual options activity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Run full pipeline (collect + analyze + email)
  python main.py --collect    Only collect today's data
  python main.py --analyze    Only run analysis (use existing data)
  python main.py --test-email Send a test email
  python main.py --status     Show database status
        """
    )

    parser.add_argument('--collect', action='store_true',
                        help='Only run data collection')
    parser.add_argument('--analyze', action='store_true',
                        help='Only run analysis (skip collection)')
    parser.add_argument('--test-email', action='store_true',
                        help='Send a test email to verify configuration')
    parser.add_argument('--status', action='store_true',
                        help='Show database status')
    parser.add_argument('--no-email', action='store_true',
                        help='Skip sending email report')

    args = parser.parse_args()

    print("=" * 60)
    print("OPTIONS VOLUME SCANNER")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initialize database
    database.init_database()

    # Handle specific commands
    if args.status:
        show_status()
        return 0

    if args.test_email:
        print("\nSending test email...")
        success = emailer.send_test_email()
        return 0 if success else 1

    if args.collect:
        # Collection only
        run_collection()
        print("\n✅ Data collection complete.")
        return 0

    if args.analyze:
        # Analysis only
        analysis_results = run_analysis()

        if not args.no_email:
            run_email_report(analysis_results)
        else:
            print("\nReport (email skipped):")
            print("-" * 40)
            print(analyzer.format_anomaly_report(analysis_results))

        return 0

    # Full pipeline (default)
    print("\nRunning full pipeline: Collect → Analyze → Report")

    # Phase 1: Collection
    collection_results = run_collection()

    if collection_results['status'] == 'skipped_weekend':
        print("\n⚠️  Skipping analysis - no new data collected (weekend).")
        return 0

    if collection_results['successful'] == 0:
        print("\n❌ No data collected. Check your internet connection.")
        return 1

    # Phase 2: Analysis
    analysis_results = run_analysis()

    # Phase 3: Email Report
    if not args.no_email:
        run_email_report(analysis_results)
    else:
        print("\nReport (email skipped):")
        print("-" * 40)
        print(analyzer.format_anomaly_report(analysis_results))

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
