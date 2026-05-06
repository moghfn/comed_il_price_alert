# ComEd Price Alert Monitor

A Python script that monitors ComEd (Commonwealth Edison) hourly electricity prices and sends email alerts when prices cross user-defined thresholds.

## Overview

This script continuously monitors the current hourly average electricity price from ComEd's API and sends email notifications when:
- The price **exceeds** your high threshold (HIGH alert)
- The price **drops below** your low threshold (LOW alert)

Perfect for users on ComEd's hourly pricing plan who want to be notified of price changes to optimize their electricity usage.

## Features

- ✅ Real-time price monitoring from ComEd's official API
- ✅ Dual threshold alerts (high and low price notifications)
- ✅ Email notifications with detailed price information
- ✅ Support for multiple email providers (Gmail, Outlook, Yahoo, custom SMTP)
- ✅ Email connection testing before monitoring starts
- ✅ Smart alert system (prevents duplicate alerts)
- ✅ Automatic alert reset when prices return to normal range
- ✅ Timestamped price updates every 60 seconds
- ✅ Graceful error handling and recovery

## Requirements

- Python 3.6 or higher
- Internet connection
- Email account for sending alerts
- Required Python packages:
  - `requests`
  - `pandas`

## Installation

1. **Clone or download this repository**

2. **Install required packages:**
   ```bash
   pip install requests pandas
   ```

   Or if using a requirements file:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the script:**
   ```bash
   python com_ed_api.py
   ```

2. **Follow the interactive prompts:**
   - Enter your **high price threshold** (alert when price goes ABOVE this)
   - Enter your **low price threshold** (alert when price goes BELOW this)
   - Enter the **recipient email address** (where alerts will be sent)
   - Select your **email provider** (1-4)
   - Enter your **sender email address**
   - Enter your **email password or app password**

3. **The script will:**
   - Test your email connection
   - Start monitoring prices every 60 seconds
   - Display current prices in real-time
   - Send email alerts when thresholds are crossed

4. **To stop monitoring:**
   - Press `Ctrl+C` in the terminal

## Email Configuration

### Gmail Setup

**⚠️ IMPORTANT:** Gmail requires an **App Password** (not your regular password).

1. Enable **2-Step Verification** on your Google account:
   - Go to: https://myaccount.google.com/security

2. Create an **App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter a name (e.g., "ComEd Price Monitor")
   - Copy the 16-character password (spaces or no spaces is fine)

3. Use this App Password when prompted by the script

### Outlook/Hotmail Setup

- If **2FA is disabled**: Use your regular password
- If **2FA is enabled**: Generate an App Password from:
  - https://account.microsoft.com/security

### Yahoo Setup

1. Generate an App Password from your Yahoo account:
   - Go to: https://login.yahoo.com/account/security
   - Navigate to App Passwords section
   - Create a new app password for "Mail"

2. Use this App Password when prompted

### Custom SMTP Setup

If you're using a different email provider:
- Select option 4 (Other/custom SMTP)
- Enter your SMTP server address
- Enter your SMTP port (usually 587 for TLS)

## How It Works

1. **Price Fetching**: The script queries ComEd's hourly pricing API every 60 seconds
2. **Threshold Checking**: Compares current price against your high and low thresholds
3. **Alert Logic**:
   - Sends an alert when price **first crosses** a threshold
   - Prevents duplicate alerts while price remains beyond threshold
   - Resets alert flags when price returns to normal range
4. **Email Notifications**: Sends formatted email alerts with:
   - Alert type (HIGH or LOW)
   - Current price
   - Threshold value
   - Timestamp

## Example Output

```
[2024-01-15 14:30:00] Current price: $0.08
[2024-01-15 14:31:00] Current price: $0.12 ⚠️  HIGH ALERT: Price $0.12 is ABOVE threshold $0.10!
   ✓ Email alert sent to user@example.com
[2024-01-15 14:32:00] Current price: $0.11
   ✓ Price has returned below high threshold
```

## Troubleshooting

### Email Authentication Failed

**For Gmail:**
- Ensure you're using an App Password (not your regular password)
- Verify 2-Step Verification is enabled
- Double-check the 16-character password (spaces or no spaces is fine)

**For Outlook/Yahoo:**
- If 2FA is enabled, use an App Password
- Verify your account security settings

**General:**
- Check your internet connection
- Verify SMTP server and port settings
- Ensure your email provider allows SMTP access

### API Connection Issues

- Check your internet connection
- Verify the ComEd API is accessible: https://hourlypricing.comed.com/api?type=currenthouraverage
- The script will continue retrying on errors

### No Data Received

- The API may be temporarily unavailable
- The script will continue monitoring and retry on the next cycle

## Notes

- The script checks prices every **60 seconds**
- Alerts are sent only when thresholds are **first crossed** (prevents spam)
- The script must remain running to continue monitoring
- For 24/7 monitoring, consider running on a server or using a process manager
- Prices are displayed in USD per kilowatt-hour (kWh)

## API Reference

The script uses ComEd's public hourly pricing API:
- **Endpoint**: `https://hourlypricing.comed.com/api?type=currenthouraverage`
- **Response Format**: JSON array with price and timestamp data

## License

This script is provided as-is for personal use. Please ensure compliance with ComEd's terms of service when using their API.

## Disclaimer

This tool is not affiliated with or endorsed by ComEd. Use at your own discretion. The script is provided for informational purposes only.

