import requests
import pandas as pd
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socket

url = "https://hourlypricing.comed.com/api?type=currenthouraverage"

# Global flag to control email sending
emails_enabled = True
stop_server_flag = False

# Get user input for price thresholds
try:
    high_threshold = float(input("Enter the price threshold for HIGH alert (alert when price goes ABOVE this): $"))
    low_threshold = float(input("Enter the price threshold for LOW alert (alert when price goes BELOW this): $"))
    # Validate thresholds
    if low_threshold >= high_threshold:
        print("Error: Low threshold must be less than high threshold.")
        exit(1)
except ValueError:
    print("Error: Please enter valid numbers for the thresholds.")
    exit(1)

# Get email configuration
recipient_email = input("\nEnter the email address to receive alerts: ").strip()
if not recipient_email:
    print("Error: Email address is required.")
    exit(1)

print("\nEmail Configuration:")
print("Select your email provider:")
print("1. Gmail")
print("2. Outlook/Hotmail")
print("3. Yahoo")
print("4. Other (custom SMTP)")

provider_choice = input("Enter choice (1-4): ").strip()

sender_email = input("Enter your email address (sender): ").strip()
sender_password = input("Enter your email password or app password: ").strip()

# Set SMTP settings based on provider
if provider_choice == "1":  # Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    print("\n⚠️  IMPORTANT for Gmail:")
    print("   - You MUST use an App Password (not your regular password)")
    print("   - Enable 2-Step Verification first")
    print("   - Create App Password at: https://myaccount.google.com/apppasswords")
    print("   - Select 'Mail' and 'Other (Custom name)' when creating")
elif provider_choice == "2":  # Outlook
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    print("\n⚠️  For Outlook/Hotmail:")
    print("   - Use your regular password if 2FA is disabled")
    print("   - If 2FA is enabled, use an App Password")
elif provider_choice == "3":  # Yahoo
    smtp_server = "smtp.mail.yahoo.com"
    smtp_port = 587
    print("\n⚠️  For Yahoo:")
    print("   - You need to generate an App Password")
    print("   - Go to: https://login.yahoo.com/account/security")
elif provider_choice == "4":  # Custom
    smtp_server = input("Enter SMTP server: ").strip()
    smtp_port = int(input("Enter SMTP port (usually 587): ").strip() or "587")
else:
    print("Invalid choice. Defaulting to Gmail settings.")
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

class StopAlertHandler(BaseHTTPRequestHandler):
    """HTTP handler for stop alert endpoint."""
    
    def do_GET(self):
        global emails_enabled
        if self.path == '/stop':
            emails_enabled = False
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Alerts Stopped</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        text-align: center;
                    }
                    h1 { color: #28a745; }
                    p { color: #666; font-size: 18px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✓ Email Alerts Stopped</h1>
                    <p>You will no longer receive price alert emails.</p>
                    <p>To resume alerts, restart the monitoring program.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = 'enabled' if emails_enabled else 'disabled'
            self.wfile.write(f'{{"emails": "{status}"}}'.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def get_local_ip():
    """Get the local IP address for the stop link."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def start_stop_server(port=8080):
    """Start HTTP server in a separate thread."""
    global stop_server_flag
    try:
        server = HTTPServer(('', port), StopAlertHandler)
        stop_server_flag = False
        server.serve_forever()
    except OSError:
        # Port might be in use, try next port
        try:
            server = HTTPServer(('', port + 1), StopAlertHandler)
            return port + 1
        except:
            return None

def test_email_connection():
    """Test email connection before starting monitoring."""
    print("\nTesting email connection...")
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        print("✓ Email connection successful!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n✗ Authentication failed!")
        print(f"  Error: {e}")
        print("\nCommon solutions:")
        if provider_choice == "1":  # Gmail
            print("  - Make sure you're using an App Password (not your regular password)")
            print("  - Enable 2-Step Verification: https://myaccount.google.com/security")
            print("  - Create App Password: https://myaccount.google.com/apppasswords")
            print("  - Copy the 16-character password (no spaces)")
        elif provider_choice == "2":  # Outlook
            print("  - If 2FA is enabled, use an App Password")
            print("  - Check: https://account.microsoft.com/security")
        elif provider_choice == "3":  # Yahoo
            print("  - Generate an App Password from your Yahoo account settings")
            print("  - Go to: https://login.yahoo.com/account/security")
        else:
            print("  - Verify your username and password are correct")
            print("  - Check if your email provider requires App Passwords")
        return False
    except smtplib.SMTPException as e:
        print(f"\n✗ SMTP Error: {e}")
        print("  - Check your SMTP server and port settings")
        return False
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print("  - Check your internet connection")
        print("  - Verify SMTP server and port are correct")
        return False

def send_email_alert(alert_type, current_price, threshold, previous_price=None, stop_url=None):
    """Send an email alert when price threshold is crossed or price changes while outside threshold."""
    global emails_enabled
    
    if not emails_enabled:
        return False
    
    # Handle case where stop_url is not available
    if stop_url is None:
        stop_url = "N/A (server not available)"
        stop_button_html = '<p style="color: #666; font-size: 12px;">Stop alert functionality is not available. Please restart the program to disable alerts.</p>'
    else:
        stop_button_html = f'<a href="{stop_url}" class="stop-button">🛑 STOP EMAIL ALERTS</a>'
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create HTML email with button
        if alert_type == "HIGH":
            msg['Subject'] = f"⚠️ HIGH PRICE ALERT - ${current_price:.2f}"
            if previous_price is not None:
                price_change = current_price - previous_price
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .price-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .stop-button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
        .stop-button:hover {{ background-color: #c82333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ HIGH PRICE ALERT</h2>
        <div class="alert-box">
            <strong>ALERT TYPE: HIGH PRICE ALERT</strong>
        </div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Previous Price:</strong> ${previous_price:.2f}</p>
            <p><strong>Price Change:</strong> ${price_change:+.2f}</p>
            <p><strong>Threshold:</strong> ${threshold:.2f}</p>
        </div>
        <p>The electricity price is above your high threshold of <strong>${threshold:.2f}</strong>.</p>
        <p>The price has changed from <strong>${previous_price:.2f}</strong> to <strong>${current_price:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">
            {stop_button_html}
        </div>
        <p style="font-size: 12px; color: #666;">Click the button above to stop receiving email alerts. You can restart alerts by running the program again.</p>
        <div class="footer">
            <p>This is an automated alert from your price monitoring system.</p>
        </div>
    </div>
</body>
</html>
"""
                plain_body = f"""
Price Alert Notification

ALERT TYPE: HIGH PRICE ALERT

Current Price: ${current_price:.2f}
Previous Price: ${previous_price:.2f}
Price Change: ${price_change:+.2f}
Threshold: ${threshold:.2f}

The electricity price is above your high threshold of ${threshold:.2f}.
The price has changed from ${previous_price:.2f} to ${current_price:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To stop receiving alerts, visit: {stop_url}

This is an automated alert from your price monitoring system.
"""
            else:
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .price-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .stop-button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
        .stop-button:hover {{ background-color: #c82333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ HIGH PRICE ALERT</h2>
        <div class="alert-box">
            <strong>ALERT TYPE: HIGH PRICE ALERT</strong>
        </div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Threshold:</strong> ${threshold:.2f}</p>
        </div>
        <p>The electricity price has exceeded your high threshold of <strong>${threshold:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">
            {stop_button_html}
        </div>
        <p style="font-size: 12px; color: #666;">Click the button above to stop receiving email alerts. You can restart alerts by running the program again.</p>
        <div class="footer">
            <p>This is an automated alert from your price monitoring system.</p>
        </div>
    </div>
</body>
</html>
"""
                plain_body = f"""
Price Alert Notification

ALERT TYPE: HIGH PRICE ALERT

Current Price: ${current_price:.2f}
Threshold: ${threshold:.2f}

The electricity price has exceeded your high threshold of ${threshold:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To stop receiving alerts, visit: {stop_url}

This is an automated alert from your price monitoring system.
"""
        else:  # LOW
            msg['Subject'] = f"⚠️ LOW PRICE ALERT - ${current_price:.2f}"
            if previous_price is not None:
                price_change = current_price - previous_price
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; }}
        .price-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .stop-button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
        .stop-button:hover {{ background-color: #c82333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ LOW PRICE ALERT</h2>
        <div class="alert-box">
            <strong>ALERT TYPE: LOW PRICE ALERT</strong>
        </div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Previous Price:</strong> ${previous_price:.2f}</p>
            <p><strong>Price Change:</strong> ${price_change:+.2f}</p>
            <p><strong>Threshold:</strong> ${threshold:.2f}</p>
        </div>
        <p>The electricity price is below your low threshold of <strong>${threshold:.2f}</strong>.</p>
        <p>The price has changed from <strong>${previous_price:.2f}</strong> to <strong>${current_price:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">
            {stop_button_html}
        </div>
        <p style="font-size: 12px; color: #666;">Click the button above to stop receiving email alerts. You can restart alerts by running the program again.</p>
        <div class="footer">
            <p>This is an automated alert from your price monitoring system.</p>
        </div>
    </div>
</body>
</html>
"""
                plain_body = f"""
Price Alert Notification

ALERT TYPE: LOW PRICE ALERT

Current Price: ${current_price:.2f}
Previous Price: ${previous_price:.2f}
Price Change: ${price_change:+.2f}
Threshold: ${threshold:.2f}

The electricity price is below your low threshold of ${threshold:.2f}.
The price has changed from ${previous_price:.2f} to ${current_price:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To stop receiving alerts, visit: {stop_url}

This is an automated alert from your price monitoring system.
"""
            else:
                html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; }}
        .price-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .stop-button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
        .stop-button:hover {{ background-color: #c82333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ LOW PRICE ALERT</h2>
        <div class="alert-box">
            <strong>ALERT TYPE: LOW PRICE ALERT</strong>
        </div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ${current_price:.2f}</p>
            <p><strong>Threshold:</strong> ${threshold:.2f}</p>
        </div>
        <p>The electricity price has dropped below your low threshold of <strong>${threshold:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">
            {stop_button_html}
        </div>
        <p style="font-size: 12px; color: #666;">Click the button above to stop receiving email alerts. You can restart alerts by running the program again.</p>
        <div class="footer">
            <p>This is an automated alert from your price monitoring system.</p>
        </div>
    </div>
</body>
</html>
"""
                plain_body = f"""
Price Alert Notification

ALERT TYPE: LOW PRICE ALERT

Current Price: ${current_price:.2f}
Threshold: ${threshold:.2f}

The electricity price has dropped below your low threshold of ${threshold:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To stop receiving alerts, visit: {stop_url}

This is an automated alert from your price monitoring system.
"""
        
        # Attach both HTML and plain text versions
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"   ✓ Email alert sent to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ✗ Authentication failed: Username or password incorrect")
        print(f"      Make sure you're using an App Password for Gmail/Outlook/Yahoo")
        return False
    except smtplib.SMTPException as e:
        print(f"   ✗ SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error sending email: {e}")
        return False

# Test email connection before starting
if not test_email_connection():
    print("\nPlease fix the email configuration and try again.")
    exit(1)

# Start HTTP server for stop functionality
server_port = 8080
local_ip = get_local_ip()
stop_url = f"http://{local_ip}:{server_port}/stop"

# Try to start server on port 8080, if busy try 8081
server_thread = None
try:
    server = HTTPServer(('', server_port), StopAlertHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"\n✓ Stop alert server started on port {server_port}")
except OSError:
    try:
        server_port = 8081
        stop_url = f"http://{local_ip}:{server_port}/stop"
        server = HTTPServer(('', server_port), StopAlertHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        print(f"\n✓ Stop alert server started on port {server_port}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not start stop alert server: {e}")
        print("   Email alerts will still work, but stop button may not function.")
        stop_url = None

print(f"\nMonitoring started...")
print(f"High alert threshold: ${high_threshold:.2f}")
print(f"Low alert threshold: ${low_threshold:.2f}")
print(f"Email alerts will be sent to: {recipient_email}")
if stop_url:
    print(f"Stop alert URL: {stop_url}")
    print("   (Recipients can click the button in emails to stop alerts)")
print(f"Press Ctrl+C to stop monitoring\n")

# Track previous price to detect changes
previous_price = None

try:
    while True:
        try:
            # Fetch current price data
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            
            # Extract price from the response
            if data and len(data) > 0:
                current_price = float(data[0]["price"])
                timestamp_ms = int(data[0]["millisUTC"])
                timestamp = pd.to_datetime(timestamp_ms, unit="ms")
                
                # Display current price
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Current price: ${current_price:.2f}", end="")
                
                # Check if price has changed
                price_changed = previous_price is not None and current_price != previous_price
                
                # Check high threshold
                if current_price > high_threshold:
                    # Send alert if: first reading, just crossed threshold, or price changed while still above threshold
                    if previous_price is None or previous_price <= high_threshold or price_changed:
                        if previous_price is None or previous_price <= high_threshold:
                            print(f" ⚠️  HIGH ALERT: Price ${current_price:.2f} is ABOVE threshold ${high_threshold:.2f}!")
                        else:
                            print(f" ⚠️  HIGH ALERT: Price changed to ${current_price:.2f} (was ${previous_price:.2f}) - still ABOVE threshold ${high_threshold:.2f}!")
                        send_email_alert("HIGH", current_price, high_threshold, previous_price, stop_url)
                    else:
                        print()
                # Check low threshold
                elif current_price < low_threshold:
                    # Send alert if: first reading, just crossed threshold, or price changed while still below threshold
                    if previous_price is None or previous_price >= low_threshold or price_changed:
                        if previous_price is None or previous_price >= low_threshold:
                            print(f" ⚠️  LOW ALERT: Price ${current_price:.2f} is BELOW threshold ${low_threshold:.2f}!")
                        else:
                            print(f" ⚠️  LOW ALERT: Price changed to ${current_price:.2f} (was ${previous_price:.2f}) - still BELOW threshold ${low_threshold:.2f}!")
                        send_email_alert("LOW", current_price, low_threshold, previous_price, stop_url)
                    else:
                        print()
                else:
                    print()
                    # Notify when price returns to normal range
                    if previous_price is not None:
                        if previous_price > high_threshold and current_price <= high_threshold:
                            print(f"   ✓ Price has returned below high threshold")
                        if previous_price < low_threshold and current_price >= low_threshold:
                            print(f"   ✓ Price has returned above low threshold")
                
                # Check if emails were disabled
                if not emails_enabled:
                    print(f"\n   ⚠️  Email alerts have been disabled via stop button.")
                    print(f"   Monitoring continues, but no emails will be sent.")
                    print(f"   Restart the program to re-enable email alerts.\n")
                
                previous_price = current_price
            else:
                print("Warning: No data received from API")
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error parsing data: {e}")
        
        # Wait 60 seconds before next check (adjust as needed)
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user.")