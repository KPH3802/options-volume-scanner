"""
Emailer Module
==============
Sends daily anomaly reports via Gmail.
Now includes Open Interest data, Put/Call ratio, and Near-term volume analysis.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config


def send_email(subject: str, body: str, html_body: str = None) -> bool:
    """
    Send an email using Gmail SMTP.
    
    Args:
        subject: Email subject line
        body: Plain text body
        html_body: Optional HTML body (for richer formatting)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_SENDER
        msg['To'] = config.EMAIL_RECIPIENT
        
        # Attach plain text version
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Attach HTML version if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Connect to Gmail SMTP server
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {config.EMAIL_RECIPIENT}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("ERROR: Gmail authentication failed!")
        print("Make sure you're using an App Password, not your regular password.")
        print("See: https://myaccount.google.com/apppasswords")
        return False
        
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False


def format_html_report(analysis_results: dict) -> str:
    """
    Format analysis results into an HTML email.
    Now includes Open Interest, Put/Call ratio, and Near-term volume data.
    """
    summary = analysis_results['summary']
    anomalies = analysis_results['anomalies']
    earnings_related = analysis_results['earnings_related']
    
    # Import here to avoid circular imports
    from analyzer import get_database_status
    db_status = get_database_status()
    
    # Check if we have OI data
    has_oi = summary.get('has_oi_data', False)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; }}
            .summary-box {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; }}
            .alert-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            .success-box {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
            .anomaly-card {{ background: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .anomaly-card h3 {{ margin: 0 0 10px 0; }}
            .signal-combined {{ border-left: 5px solid #e74c3c; }}
            .signal-combined h3 {{ color: #c0392b; }}
            .signal-volume {{ border-left: 5px solid #f39c12; }}
            .signal-volume h3 {{ color: #d68910; }}
            .signal-oi {{ border-left: 5px solid #e67e22; }}
            .signal-oi h3 {{ color: #ca6f1e; }}
            .signal-putcall {{ border-left: 5px solid #3498db; }}
            .signal-putcall h3 {{ color: #2980b9; }}
            .signal-nearterm {{ border-left: 5px solid #9b59b6; }}
            .signal-nearterm h3 {{ color: #8e44ad; }}
            .metric {{ display: inline-block; margin-right: 20px; margin-bottom: 10px; }}
            .metric-label {{ font-size: 0.85em; color: #666; }}
            .metric-value {{ font-size: 1.2em; font-weight: bold; }}
            .metric-value.positive {{ color: #27ae60; }}
            .metric-value.negative {{ color: #e74c3c; }}
            .metric-value.bearish {{ color: #e74c3c; }}
            .metric-value.bullish {{ color: #27ae60; }}
            .flag {{ background: #e74c3c; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; margin-right: 5px; }}
            .flag-combined {{ background: #e74c3c; }}
            .flag-volume {{ background: #f39c12; }}
            .flag-oi {{ background: #e67e22; }}
            .flag-putcall {{ background: #3498db; }}
            .flag-nearterm {{ background: #9b59b6; }}
            .earnings-flag {{ background: #3498db; }}
            .signal-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: white; margin-bottom: 10px; margin-right: 5px; }}
            .badge-combined {{ background: #e74c3c; }}
            .badge-volume {{ background: #f39c12; }}
            .badge-oi {{ background: #e67e22; }}
            .badge-putcall {{ background: #3498db; }}
            .badge-nearterm {{ background: #9b59b6; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background: #f8f9fa; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 0.85em; color: #666; }}
            .section-header {{ background: #f8f9fa; padding: 10px 15px; margin: 25px 0 15px 0; border-radius: 4px; }}
            .oi-note {{ background: #e8f4f8; border-left: 4px solid #17a2b8; padding: 10px 15px; margin: 15px 0; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Options Volume Anomaly Report</h1>
            <p><strong>Date:</strong> {summary['trade_date']}</p>
            
            <div class="summary-box">
                <h2 style="margin-top: 0;">Summary</h2>
                <div class="metric">
                    <div class="metric-label">Tickers Analyzed</div>
                    <div class="metric-value">{summary['analyzed']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Anomalies Found</div>
                    <div class="metric-value">{summary['anomalies_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Earnings-Related</div>
                    <div class="metric-value">{summary['earnings_related_count']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Days of Data</div>
                    <div class="metric-value">{db_status['total_days_collected']}</div>
                </div>
    """
    
    # Add signal type breakdown if we have data
    if has_oi:
        html += f"""
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                    <strong>Signal Breakdown:</strong><br>
                    <span class="signal-badge badge-combined">🔴 Combined: {summary.get('combined_count', 0)}</span>
                    <span class="signal-badge badge-volume">🟡 Volume: {summary.get('volume_only_count', 0)}</span>
                    <span class="signal-badge badge-oi">🟠 OI Surge: {summary.get('oi_surge_count', 0)}</span>
                    <span class="signal-badge badge-putcall">🔵 P/C Extreme: {summary.get('putcall_count', 0)}</span>
                    <span class="signal-badge badge-nearterm">⚡ Near-term: {summary.get('nearterm_count', 0)}</span>
                </div>
        """
    
    html += """
            </div>
    """
    
    # OI tracking status note
    if not has_oi:
        html += """
            <div class="oi-note">
                <strong>📈 Open Interest Tracking:</strong> Starting today! After a few days of OI data collection, 
                you'll see combined signals (Volume + OI) which are stronger indicators of new position building.
            </div>
        """
    
    # Anomalies section
    if anomalies:
        html += """
            <div class="alert-box">
                <h2 style="margin-top: 0;">🚨 Anomalies Detected</h2>
                <p>The following tickers have unusual options activity that may warrant investigation:</p>
            </div>
        """
        
        # Group by signal type
        combined = [a for a in anomalies if a.get('signal_type') == 'combined']
        volume_only = [a for a in anomalies if a.get('signal_type') == 'volume_only']
        oi_surge = [a for a in anomalies if a.get('signal_type') == 'oi_surge']
        putcall = [a for a in anomalies if a.get('signal_type') == 'putcall_extreme']
        nearterm = [a for a in anomalies if a.get('signal_type') == 'nearterm_spike']
        
        # Combined signals (strongest)
        if combined:
            html += """
            <div class="section-header">
                <strong>🔴 COMBINED SIGNALS</strong> - Volume Spike + OI Increase (Strongest - New Positions)
            </div>
            """
            for a in combined[:10]:
                html += _format_anomaly_card(a, 'combined', has_oi)
        
        # Volume only signals
        if volume_only:
            html += """
            <div class="section-header">
                <strong>🟡 VOLUME ONLY SIGNALS</strong> - Volume Spike (Could be closing trades)
            </div>
            """
            for a in volume_only[:10]:
                html += _format_anomaly_card(a, 'volume', has_oi)
        
        # OI surge signals
        if oi_surge:
            html += """
            <div class="section-header">
                <strong>🟠 OI SURGE</strong> - Open Interest Building (Accumulation Pattern)
            </div>
            """
            for a in oi_surge[:5]:
                html += _format_anomaly_card(a, 'oi', has_oi)
        
        # Put/Call extreme signals
        if putcall:
            html += """
            <div class="section-header">
                <strong>🔵 PUT/CALL EXTREME</strong> - Unusual Put/Call Ratio
            </div>
            """
            for a in putcall[:5]:
                html += _format_anomaly_card(a, 'putcall', has_oi)
        
        # Near-term spike signals
        if nearterm:
            html += """
            <div class="section-header">
                <strong>⚡ NEAR-TERM SPIKE</strong> - Short-dated Options Focus (Speculative)
            </div>
            """
            for a in nearterm[:5]:
                html += _format_anomaly_card(a, 'nearterm', has_oi)
    
    else:
        html += """
            <div class="success-box">
                <h2 style="margin-top: 0;">✅ No Anomalies Detected</h2>
                <p>All tickers are within normal volume ranges today.</p>
            </div>
        """
    
    # Earnings-related section
    if earnings_related:
        html += f"""
            <div class="section-header">
                <strong>📅 EARNINGS-RELATED</strong> - High volume near earnings (expected behavior)
            </div>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Volume</th>
                    <th>% Above Avg</th>
                    <th>Signal Type</th>
                </tr>
        """
        for e in earnings_related[:10]:
            signal_type = e.get('signal_type', 'volume_only')
            html += f"""
                <tr>
                    <td><strong>{e['ticker']}</strong></td>
                    <td>{e['volume_today']:,}</td>
                    <td>+{e['percentage_above']:.0f}%</td>
                    <td>{signal_type}</td>
                </tr>
            """
        html += "</table>"
    
    # Footer
    html += f"""
            <div class="footer">
                <p><strong>Signal Types:</strong></p>
                <ul>
                    <li>🔴 <strong>Combined</strong> - Volume spike + OI increase (strongest signal - new positions opening)</li>
                    <li>🟡 <strong>Volume Only</strong> - Volume spike without OI change (could be closing trades)</li>
                    <li>🟠 <strong>OI Surge</strong> - Open interest building without volume spike (accumulation)</li>
                    <li>🔵 <strong>Put/Call Extreme</strong> - Unusual put/call ratio (sentiment indicator)</li>
                    <li>⚡ <strong>Near-term Spike</strong> - High concentration in short-dated options (speculative)</li>
                </ul>
                <p><em>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def _format_anomaly_card(a: dict, signal_type: str, has_oi: bool) -> str:
    """Format a single anomaly as an HTML card."""
    signal_class = {
        'combined': 'signal-combined',
        'volume': 'signal-volume',
        'oi': 'signal-oi',
        'putcall': 'signal-putcall',
        'nearterm': 'signal-nearterm'
    }.get(signal_type, 'signal-volume')
    
    html = f"""
    <div class="anomaly-card {signal_class}">
        <h3>{a['ticker']}</h3>
        <div class="metric">
            <div class="metric-label">Volume Today</div>
            <div class="metric-value">{a['volume_today']:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Deviation</div>
            <div class="metric-value">{a['deviation_multiple']:.1f}σ</div>
        </div>
        <div class="metric">
            <div class="metric-label">% Above Avg</div>
            <div class="metric-value">{a['percentage_above']:.0f}%</div>
        </div>
    """
    
    # Add OI metrics if available
    if has_oi:
        oi_today = a.get('oi_today', 0)
        oi_change = a.get('oi_change_pct', 0)
        oi_class = 'positive' if oi_change > 0 else 'negative' if oi_change < 0 else ''
        
        html += f"""
        <div class="metric">
            <div class="metric-label">Open Interest</div>
            <div class="metric-value">{oi_today:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">OI Change</div>
            <div class="metric-value {oi_class}">{oi_change:+.1f}%</div>
        </div>
        """
    
    # Add Put/Call ratio if available
    if a.get('putcall_ratio') is not None:
        pc_ratio = a['putcall_ratio']
        pc_class = 'bearish' if pc_ratio > 1 else 'bullish' if pc_ratio < 1 else ''
        html += f"""
        <div class="metric">
            <div class="metric-label">Put/Call Ratio</div>
            <div class="metric-value {pc_class}">{pc_ratio:.2f}</div>
        </div>
        """
    
    # Add Near-term ratio if available
    if a.get('nearterm_ratio') is not None:
        nt_ratio = a['nearterm_ratio']
        html += f"""
        <div class="metric">
            <div class="metric-label">Near-term %</div>
            <div class="metric-value">{nt_ratio*100:.0f}%</div>
        </div>
        """
    
    # Add flags
    flags_html = ''.join([f'<span class="flag">{f}</span>' for f in a.get('flags', [])])
    if flags_html:
        html += f'<div style="margin-top: 10px;">{flags_html}</div>'
    
    html += "</div>"
    return html


def send_daily_report(analysis_results: dict) -> bool:
    """
    Send the daily anomaly report email.
    
    Args:
        analysis_results: Results from analyzer.analyze_all_tickers()
    
    Returns:
        True if email sent successfully
    """
    # Check if we're still in baseline collection mode
    if analysis_results.get('baseline_mode'):
        days_collected = analysis_results.get('days_collected', 0)
        days_required = analysis_results.get('days_required', 30)
        has_oi = analysis_results.get('has_oi_data', False)
        
        subject = f"⏳ Options Scanner - Baseline Collection ({days_collected}/{days_required} days)"
        plain_body = f"""Options Volume Scanner - Baseline Collection Status

Currently collecting baseline data: {days_collected}/{days_required} trading days
Open Interest tracking: {'Active' if has_oi else 'Starting'}

Anomaly detection requires {days_required} days of historical data to establish 
reliable statistical baselines. Once sufficient data is collected, you will 
begin receiving daily anomaly reports.

Estimated completion: ~{days_required - days_collected} more trading days
"""
        html_body = f"""<html><body>
<h2>⏳ Options Volume Scanner - Baseline Collection</h2>
<p>Currently collecting baseline data: <strong>{days_collected}/{days_required}</strong> trading days</p>
<p>Open Interest tracking: <strong>{'Active ✓' if has_oi else 'Starting today'}</strong></p>
<p>Anomaly detection requires {days_required} days of historical data to establish 
reliable statistical baselines.</p>
<p>Once sufficient data is collected, you will begin receiving daily anomaly reports 
with combined Volume + Open Interest signals.</p>
<p><em>Estimated completion: ~{days_required - days_collected} more trading days</em></p>
</body></html>"""
        return send_email(subject, plain_body, html_body)
    
    from analyzer import format_anomaly_report
    
    summary = analysis_results['summary']
    anomaly_count = summary['anomalies_count']
    has_oi = summary.get('has_oi_data', False)
    
    # Create subject line with signal type info if available
    if anomaly_count > 0:
        if has_oi:
            combined = summary.get('combined_count', 0)
            putcall = summary.get('putcall_count', 0)
            nearterm = summary.get('nearterm_count', 0)
            
            if combined > 0:
                subject = f"🔴 Options Alert: {combined} Combined Signals + {anomaly_count - combined} Others - {summary['trade_date']}"
            elif putcall > 0:
                subject = f"🔵 Options Alert: {putcall} Put/Call Extreme + {anomaly_count - putcall} Others - {summary['trade_date']}"
            elif nearterm > 0:
                subject = f"⚡ Options Alert: {nearterm} Near-term Spikes + {anomaly_count - nearterm} Others - {summary['trade_date']}"
            else:
                subject = f"🟡 Options Alert: {anomaly_count} Volume Anomalies - {summary['trade_date']}"
        else:
            subject = f"🚨 Options Alert: {anomaly_count} Anomalies Detected - {summary['trade_date']}"
    else:
        subject = f"✅ Options Report: No Anomalies - {summary['trade_date']}"
    
    # Generate both plain text and HTML versions
    plain_body = format_anomaly_report(analysis_results)
    html_body = format_html_report(analysis_results)
    
    return send_email(subject, plain_body, html_body)


def send_test_email() -> bool:
    """
    Send a test email to verify configuration.
    """
    subject = "🧪 Options Scanner - Test Email"
    body = """
This is a test email from the Options Volume Scanner.

If you received this email, your email configuration is working correctly!

Configuration:
- SMTP Server: {server}
- Sender: {sender}
- Recipient: {recipient}

Next steps:
1. Run the data collector to start gathering options volume data
2. After a few days of data collection, the analyzer will be able to detect anomalies
3. You'll receive daily reports automatically

Happy scanning!
    """.format(
        server=config.SMTP_SERVER,
        sender=config.EMAIL_SENDER,
        recipient=config.EMAIL_RECIPIENT
    )
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #27ae60; }}
            .success-box {{ background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; }}
            .config-table {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Test Email Successful!</h1>
            
            <div class="success-box">
                <p><strong>Your email configuration is working correctly.</strong></p>
                <p>You will receive daily options volume anomaly reports at this address.</p>
            </div>
            
            <div class="config-table">
                <h3>Current Configuration:</h3>
                <p><strong>SMTP Server:</strong> {config.SMTP_SERVER}</p>
                <p><strong>Sender:</strong> {config.EMAIL_SENDER}</p>
                <p><strong>Recipient:</strong> {config.EMAIL_RECIPIENT}</p>
            </div>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Run the data collector daily to gather options volume data</li>
                <li>After a few days, the analyzer will detect anomalies</li>
                <li>Daily reports will be sent automatically</li>
            </ol>
            
            <p>Happy scanning! 📊</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, body, html_body)


if __name__ == "__main__":
    print("Testing email configuration...")
    print(f"Sender: {config.EMAIL_SENDER}")
    print(f"Recipient: {config.EMAIL_RECIPIENT}")
    
    # Check if credentials are configured
    if "your_email" in config.EMAIL_SENDER or "xxxx" in config.EMAIL_PASSWORD:
        print("\n⚠️  WARNING: Email credentials not configured!")
        print("Please edit config.py and set your Gmail address and App Password.")
        print("\nTo create an App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Select 'Mail' and your device")
        print("3. Copy the 16-character password")
        print("4. Paste it in config.py as EMAIL_PASSWORD")
    else:
        print("\nSending test email...")
        success = send_test_email()
        if success:
            print("✅ Test email sent! Check your inbox.")
        else:
            print("❌ Failed to send test email. Check your configuration.")
