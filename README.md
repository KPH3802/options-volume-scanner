# Options Volume Scanner

**Python tool that monitors unusual options trading volume across S&P 500 stocks. Detects anomalies using statistical methods, adjusts for day-of-week patterns and earnings windows, and delivers daily HTML email reports.**

Options volume spikes can precede significant price moves. This scanner ingests daily options volume for the full S&P 500, compares it against rolling historical averages, and surfaces statistically significant anomalies — separating signal from routine earnings-driven noise.

---

## What It Detects

| Detection Method | Description |
|-----------------|-------------|
| **Standard Deviation Threshold** | Volume exceeding 2.5 std devs above rolling mean |
| **Percentage Threshold** | Volume 200%+ above historical average |
| **Day-of-Week Adjustment** | Normalizes for Friday expiry-driven volume spikes |
| **Earnings Calendar Filter** | Excludes expected high-volume windows around earnings |

Anomalies are ranked by severity and delivered via HTML email report, including today's volume, historical average, standard deviations above mean, and percentage above average.

---

## Backtest Results: Signal Not Validated

The unusual options volume signal was backtested against S&P 500 stocks from 2020 through 2025.

**Result: t-statistic = -0.44 — not statistically significant.**

The signal showed no consistent predictive edge in the 2025 regime. Options volume anomalies that historically preceded price moves appear to have been priced out as the market became more efficient at absorbing this information. This scanner is **archived as a research project**; no live trading strategy is deployed from it.

The infrastructure (data pipeline, anomaly detection, database) remains production-quality and is available as a foundation for further research into options flow signals.

---

## Architecture

```
main.py               # Orchestrator — collect → analyze → email pipeline
├── data_collector.py  # Pulls options volume from Yahoo Finance for S&P 500
├── database.py        # SQLite storage and historical baseline queries
├── analyzer.py        # Standard deviation + percentage anomaly detection
├── emailer.py         # HTML email report builder + SMTP delivery
└── config.py          # Thresholds and credentials (not committed)
```

---

## Setup

```bash
git clone https://github.com/KPH3802/options-volume-scanner.git
cd options-volume-scanner
pip install -r requirements.txt
cp config_example.py config.py
python main.py
python main.py --collect       # Only collect today's data
python main.py --analyze       # Only analyze existing data
python main.py --no-email      # Run without sending email
python main.py --status        # Show database status
python main.py --test-email    # Send test email
```

### Requirements
- Python 3.8+
- Yahoo Finance access via yfinance (free, ~15 min delay)
- Gmail account with App Password for alerts

---

## Configuration

Key thresholds in `config.py`:

```python
STD_DEV_THRESHOLD = 2.5       # Flag if volume exceeds N std devs above mean
PERCENTAGE_THRESHOLD = 200    # Flag if volume is N% above average
MIN_AVERAGE_VOLUME = 100      # Filter illiquid options
```

---

## Disclaimer

This tool is for **educational and research purposes only**. Unusual options volume does not constitute evidence of insider trading or predictive information. This project does not constitute financial advice. Always do your own research.

---

## License

MIT
