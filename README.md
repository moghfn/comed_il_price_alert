# ComEd Price Monitor

A Python script that monitors ComEd hourly electricity prices and sends email alerts when prices cross your specified thresholds.

## Features

- 📊 Real-time monitoring of ComEd hourly electricity prices
- 📧 Email alerts when prices go above or below your thresholds
- 👥 Support for multiple email recipients
- 🔔 Customizable high and low price thresholds
- 🛑 Stop alerts feature via email link
- 🔄 Runs continuously in the background
- 💰 Displays prices in cents (¢)

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/comed-price-monitor.git
cd comed-price-monitor
```

2. Install required dependencies:
```bash
pip3 install requests
```

## Gmail App Password Setup

If using Gmail, you **must** use an App Password (not your regular password):

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Other (Custom name)"
4. Copy the 16-character password (no spaces needed in the command)

## Usage

### Basic Usage

```bash
python3 comed_tracker.py -u <upper_threshold> -l <lower_threshold> -e <recipient_email>
```

The script will prompt you for sender email and password.

### Full Command (No Prompts)

```bash
python3 comed_tracker.py -u 2.8 -l 0 -e "recipient@gmail.com" -s sender@gmail.com -p "your-app-password"
```

### Multiple Recipients

```bash
python3 comed_tracker.py -u 2.8 -l 0 -e "email1@gmail.com, email2@yahoo.com, email3@outlook.com" -s sender@gmail.com -p "your-app-password"
```

### Negative Thresholds

You can use negative values for the lower threshold:

```bash
python3 comed_tracker.py --upper 3 --lower -0.5 -e "recipient@gmail.com"
```

### Command-Line Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--upper` | `-u` | Upper price threshold (alert when price goes ABOVE) | Yes |
| `--lower` | `-l` | Lower price threshold (alert when price goes BELOW) | Yes |
| `--email` | `-e` | Recipient email(s), comma-separated | Yes |
| `--sender` | `-s` | Sender email address | No* |
| `--password` | `-p` | Sender email password/app password | No* |
| `--provider` | | Email provider: `gmail`, `outlook`, `yahoo`, `custom` | No (default: gmail) |
| `--smtp-server` | | Custom SMTP server (if provider is `custom`) | No |
| `--smtp-port` | | SMTP port | No (default: 587) |

*If not provided, the script will prompt for these values.

## Running in Background

### Option 1: Using `nohup` (Simple)

```bash
nohup python3 -u comed_tracker.py -u 2.8 -l 0 -e "your@email.com" -s sender@gmail.com -p "app-password" > monitor.log 2>&1 &
```

Check the log:
```bash
tail -f monitor.log
```

Stop the script:
```bash
pkill -f comed_tracker.py
```

### Option 2: Using `screen` (Recommended)

```bash
# Start a screen session
screen -S price_monitor

# Run the script
python3 comed_tracker.py -u 2.8 -l 0 -e "your@email.com" -s sender@gmail.com -p "app-password"

# Detach: Press Ctrl+A then D
# Reconnect anytime: screen -r price_monitor
```

### Option 3: Systemd Service (Auto-start on boot)

Create `/etc/systemd/system/comed-monitor.service`:

```ini
[Unit]
Description=ComEd Price Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/comed_tracker.py -u 2.8 -l 0 -e your@email.com -s sender@gmail.com -p "app-password"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable comed-monitor.service
sudo systemctl start comed-monitor.service
sudo systemctl status comed-monitor.service
```

## How It Works

1. The script checks the ComEd API every 60 seconds for the current hourly average price
2. When the price crosses your thresholds, it sends an email alert to all recipients
3. Each email includes a "Stop Alerts" button that disables future emails
4. The script continues monitoring until manually stopped

## Email Alert Examples

**HIGH Price Alert** - Sent when price goes above your upper threshold
- Subject: ⚠️ HIGH PRICE ALERT - ¢3.50
- Includes current price, threshold, and timestamp

**LOW Price Alert** - Sent when price goes below your lower threshold
- Subject: ⚠️ LOW PRICE ALERT - ¢0.25
- Includes current price, threshold, and timestamp

## Stopping Alerts

You can stop email alerts in two ways:

1. **Via Email Link**: Click the "🛑 STOP EMAIL ALERTS" button in any alert email
2. **Stop the Script**: 
   - If running in foreground: Press `Ctrl+C`
   - If running with nohup: `pkill -f comed_tracker.py`
   - If running with screen: `screen -r price_monitor` then `Ctrl+C`
   - If running as service: `sudo systemctl stop comed-monitor.service`

## Troubleshooting

### Authentication Failed
- Make sure you're using an App Password, not your regular Gmail password
- Verify 2-Step Verification is enabled
- Check that you copied the App Password correctly (16 characters)

### No Log Output with `nohup`
Use the `-u` flag with Python to disable buffering:
```bash
nohup python3 -u comed_tracker.py ... > monitor.log 2>&1 &
```

### Port Already in Use
The script uses port 8080 for the stop alert feature. If unavailable, it tries 8081. This is normal.

### Negative Threshold Issues
Use the long form `--lower -0.5` or `--` separator to avoid argument parsing issues.

## Security Notes

- **Never commit your passwords or credentials to GitHub**
- Use App Passwords instead of your main account password
- Consider using environment variables or config files for credentials
- Keep your `monitor.log` file private (it may contain email addresses)

## License

MIT License - Feel free to modify and distribute

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Disclaimer

This script is not affiliated with ComEd. Electricity prices are fetched from the public ComEd API. Use at your own risk.

## Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This script checks prices every 60 seconds. You can modify the `time.sleep(60)` value in the code to change the frequency.
