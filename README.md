# Options Volume Scanner 📊

A Python tool that monitors unusual options trading volume on S&P 500 stocks to identify potential informed trading activity.

## What It Does

Every trading day, this scanner:
1. **Collects** options volume data for all ~500 S&P 500 stocks
2. **Analyzes** today's volume against historical averages
3. **Detects** anomalies using statistical methods
4. **Emails** you a report of any suspicious activity

The goal is to spot unusual options activity that *might* indicate someone trading on non-public information, similar to how regulators monitor for insider trading.

## Features

- ✅ Pulls options data from Yahoo Finance (free)
- ✅ Maintains historical database for comparison
- ✅ Day-of-week volume adjustments
- ✅ Earnings calendar awareness (filters expected high volume)
- ✅ Dual detection: standard deviation AND percentage thresholds
- ✅ Beautiful HTML email reports
- ✅ SQLite database (no server required)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email (Optional but Recommended)

Edit `config.py` and set your Gmail credentials:

```python
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"  # App Password, NOT your regular password!
EMAIL_RECIPIENT = "your_email@gmail.com"
```

**Important:** You need a Gmail App Password, not your regular password:
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2-Factor Authentication if not already enabled
3. Create an App Password for "Mail"
4. Copy the 16-character password

### 3. Test Email Configuration

```bash
python main.py --test-email
```

### 4. Run Your First Collection

```bash
python main.py --collect
```

This will take ~15-30 minutes to fetch data for all 500 stocks.

### 5. Check Status

```bash
python main.py --status
```

### 6. Run Full Pipeline

```bash
python main.py
```

## Command Reference

| Command | Description |
|---------|-------------|
| `python main.py` | Full pipeline: collect → analyze → email |
| `python main.py --collect` | Only collect today's data |
| `python main.py --analyze` | Only analyze existing data |
| `python main.py --test-email` | Send test email |
| `python main.py --status` | Show database status |
| `python main.py --no-email` | Run without sending email |

## Automation with PythonAnywhere (Recommended)

PythonAnywhere is the easiest way to run this automatically every day.

### Setup Steps

1. **Create a free account** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload your files** via the Files tab:
   - Upload all `.py` files
   - Upload `requirements.txt`

3. **Open a Bash console** and install dependencies:
   ```bash
   pip3 install --user -r requirements.txt
   ```

4. **Test the script**:
   ```bash
   cd ~/options_scanner
   python3 main.py --status
   python3 main.py --collect  # Run a test collection
   ```

5. **Set up scheduled task** (Tasks tab):
   - Time: 21:30 UTC (4:30 PM ET, after market close)
   - Command: `cd ~/options_scanner && python3 main.py`

That's it! The script will run automatically every trading day.

### PythonAnywhere Free Tier Limits

- ✅ 1 scheduled task per day (perfect for us)
- ✅ 512 MB disk space (plenty for SQLite)
- ✅ Outbound internet access (for Yahoo Finance)
- ⚠️ CPU limited to 100 seconds/day (usually enough)

## Configuration Options

All settings are in `config.py`:

### Detection Thresholds

```python
# Flag if volume is this many standard deviations above mean
STD_DEV_THRESHOLD = 2.5

# Flag if volume is this percentage above average
PERCENTAGE_THRESHOLD = 200  # 200% = 2x average

# Minimum average volume to consider (filters illiquid options)
MIN_AVERAGE_VOLUME = 100
```

### Historical Periods

```python
MIN_DAYS_FOR_AVERAGE = {
    "1_week": 3,    # Need 3 days for 1-week average
    "1_month": 10,  # Need 10 days for 1-month average
    "3_month": 30,
    "6_month": 60,
}
```

### Day-of-Week Adjustments

```python
DAY_OF_WEEK_FACTORS = {
    0: 1.05,  # Monday - slightly higher
    1: 1.00,  # Tuesday - baseline
    2: 1.00,  # Wednesday - baseline
    3: 1.05,  # Thursday - slightly higher
    4: 1.15,  # Friday - higher (weekly expiry)
}
```

## Understanding the Output

### Anomaly Report

The email report includes:

1. **Summary Stats** - How many tickers analyzed and anomalies found

2. **Anomalies** - Stocks with suspicious volume:
   - Today's volume
   - Historical average
   - Standard deviations above mean
   - Percentage above average

3. **Earnings-Related** - High volume near earnings (expected, not suspicious)

### Example Alert

```
🚨 ANOMALY: CVX (Chevron)
  Today's Volume: 450,000
  1-Month Avg: 85,000
  Deviation: 4.2 std devs
  % Above Avg: 429%
  Flags: 4.2 std devs above mean, 429% above average
```

## Database Schema

The SQLite database (`options_data.db`) contains:

- **daily_options_volume** - Daily volume data per ticker
- **earnings_calendar** - Known earnings dates
- **anomalies** - Historical record of detected anomalies
- **sp500_tickers** - S&P 500 constituent tracking

## Limitations & Disclaimers

⚠️ **This is for educational/research purposes only.**

- Yahoo Finance data has a ~15 minute delay
- Not all unusual volume indicates insider trading
- Many anomalies have legitimate explanations (news, analyst upgrades, etc.)
- This tool cannot distinguish legal from illegal trading
- Past anomaly patterns don't guarantee future predictive value

## Troubleshooting

### "No data collected"

- Check your internet connection
- Yahoo Finance may be rate-limiting you (wait and retry)
- Weekend? Market is closed!

### "Email failed to send"

- Verify App Password is correct (not regular password)
- Check 2FA is enabled on your Google account
- Gmail may block "less secure apps" - use App Password

### "Insufficient historical data"

- Normal during ramp-up period
- Wait a few more trading days
- Analysis improves with more data

## Future Enhancements

Ideas for future development:

- [ ] Put/Call ratio analysis
- [ ] Open Interest changes
- [ ] Near-term vs far-dated volume split
- [ ] Sector-level aggregation
- [ ] News correlation (check if anomaly preceded news)
- [ ] Web dashboard for visualization
- [ ] Backtesting against historical events

## License

MIT License - Use freely, no warranty.

---

*Built to explore whether unusual options activity has predictive value. Use responsibly.*
