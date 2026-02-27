"""
Options Scanner Configuration
=============================
Copy this file to config.py and fill in your credentials.

    cp config_example.py config.py
"""

# =============================================================================
# EMAIL SETTINGS
# =============================================================================
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password_here"
EMAIL_RECIPIENT = "your_email@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =============================================================================
# ANOMALY DETECTION THRESHOLDS
# =============================================================================
STD_DEV_THRESHOLD = 2.5
PERCENTAGE_THRESHOLD = 200
MIN_AVERAGE_VOLUME = 100
MIN_BASELINE_DAYS = 30

MIN_DAYS_FOR_AVERAGE = {
    "1_week": 3,
    "1_month": 10,
    "3_month": 30,
    "6_month": 60,
}

# =============================================================================
# DATA COLLECTION SETTINGS
# =============================================================================
API_DELAY = 0.5
MAX_RETRIES = 3
DATABASE_PATH = "options_data.db"

# =============================================================================
# DAY OF WEEK ADJUSTMENTS
# =============================================================================
DAY_OF_WEEK_FACTORS = {
    0: 1.05,  # Monday
    1: 1.00,  # Tuesday
    2: 1.00,  # Wednesday
    3: 1.05,  # Thursday
    4: 1.15,  # Friday (weekly expiry)
    5: 0.00,  # Saturday
    6: 0.00,  # Sunday
}

# =============================================================================
# EARNINGS EXCLUSION SETTINGS
# =============================================================================
EARNINGS_EXCLUSION_DAYS_BEFORE = 3
EARNINGS_EXCLUSION_DAYS_AFTER = 1
