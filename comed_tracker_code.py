import requests
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socket
import argparse

url = "https://hourlypricing.comed.com/api?type=currenthouraverage"

# Global flag to control email sending
emails_enabled = True
stop_server_flag = False

# Parse command line arguments
parser = argparse.ArgumentParser(description='Monitor ComEd electricity prices and send email alerts')
parser.add_argument('--upper', '-u', type=float, required=True, 
                    help='Upper price threshold (alert when price goes ABOVE this)')
parser.add_argument('--lower', '-l', type=float, required=True,
                    help='Lower price threshold (alert when price goes BELOW this)')
parser.add_argument('--email', '-e', type=str, required=True,
                    help='Email address(es) to receive alerts (comma-separated for multiple)')
parser.add_argument('--sender', '-s', type=str, required=False,
                    help='Sender email address (optional, will prompt if not provided)')
parser.add_argument('--password', '-p', type=str, required=False,
                    help='Sender email password (optional, will prompt if not provided)')
parser.add_argument('--provider', type=str, choices=['gmail', 'outlook', 'yahoo', 'custom'],
                    default='gmail', help='Email provider (default: gmail)')
parser.add_argument('--smtp-server', type=str, required=False,
                    help='Custom SMTP server (required if provider is "custom")')
parser.add_argument('--smtp-port', type=int, default=587,
                    help='SMTP port (default: 587)')

args = parser.parse_args()

# Validate thresholds
high_threshold = args.upper
low_threshold = args.lower
if low_threshold >= high_threshold:
    print("Error: Lower threshold must be less than upper threshold.")
    exit(1)

recipient_email = args.email

# Parse multiple email addresses (comma-separated)
recipient_emails = [email.strip() for email in recipient_email.split(',')]
print(f"\nRecipient(s): {', '.join(recipient_emails)}")

# Get sender credentials (prompt if not provided via command line)
if args.sender:
    sender_email = args.sender
else:
    sender_email = input("Enter your email address (sender): ").strip()

if args.password:
    sender_password = args.password
else:
    sender_password = input("Enter your email password or app password: ").strip()

# Set SMTP settings based on provider
if args.provider == 'gmail':
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    print("\n⚠️  IMPORTANT for Gmail:")
    print("   - You MUST use an App Password (not your regular password)")
    print("   - Enable 2-Step Verification first")
    print("   - Create App Password at: https://myaccount.google.com/apppasswords")
elif args.provider == 'outlook':
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    print("\n⚠️  For Outlook/Hotmail:")
    print("   - Use your regular password if 2FA is disabled")
    print("   - If 2FA is enabled, use an App Password")
elif args.provider == 'yahoo':
    smtp_server = "smtp.mail.yahoo.com"
    smtp_port = 587
    print("\n⚠️  For Yahoo:")
    print("   - You need to generate an App Password")
elif args.provider == 'custom':
    if not args.smtp_server:
        print("Error: --smtp-server is required when using custom provider")
        exit(1)
    smtp_server = args.smtp_server
    smtp_port = args.smtp_port

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
        pass

def get_local_ip():
    """Get the local IP address for the stop link."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

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
        if args.provider == 'gmail':
            print("  - Make sure you're using an App Password (not your regular password)")
            print("  - Enable 2-Step Verification: https://myaccount.google.com/security")
            print("  - Create App Password: https://myaccount.google.com/apppasswords")
        elif args.provider == 'outlook':
            print("  - If 2FA is enabled, use an App Password")
        elif args.provider == 'yahoo':
            print("  - Generate an App Password from your Yahoo account settings")
        return False
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        return False

def send_email_alert(alert_type, current_price, threshold, previous_price=None, stop_url=None):
    """Send an email alert."""
    global emails_enabled
    
    if not emails_enabled:
        return False
    
    if stop_url is None:
        stop_button_html = '<p style="color: #666; font-size: 12px;">Stop alert functionality not available.</p>'
    else:
        stop_button_html = f'<a href="{stop_url}" class="stop-button">🛑 STOP EMAIL ALERTS</a>'
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        
        if alert_type == "HIGH":
            msg['Subject'] = f"⚠️ HIGH PRICE ALERT - ¢{current_price:.2f}"
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
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ HIGH PRICE ALERT</h2>
        <div class="alert-box"><strong>ALERT TYPE: HIGH PRICE ALERT</strong></div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ¢{current_price:.2f}</p>
            <p><strong>Threshold:</strong> ¢{threshold:.2f}</p>
        </div>
        <p>The electricity price has exceeded your high threshold of <strong>¢{threshold:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">{stop_button_html}</div>
    </div>
</body>
</html>
"""
        else:
            msg['Subject'] = f"⚠️ LOW PRICE ALERT - ¢{current_price:.2f}"
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
    </style>
</head>
<body>
    <div class="container">
        <h2>⚠️ LOW PRICE ALERT</h2>
        <div class="alert-box"><strong>ALERT TYPE: LOW PRICE ALERT</strong></div>
        <div class="price-info">
            <p><strong>Current Price:</strong> ¢{current_price:.2f}</p>
            <p><strong>Threshold:</strong> ¢{threshold:.2f}</p>
        </div>
        <p>The electricity price has dropped below your low threshold of <strong>¢{threshold:.2f}</strong>.</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="text-align: center; margin: 30px 0;">{stop_button_html}</div>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_emails, msg.as_string())
        server.quit()
        
        print(f"   ✓ Email alert sent to {len(recipient_emails)} recipient(s)")
        return True
    except Exception as e:
        print(f"   ✗ Error sending email: {e}")
        return False

# Test email connection
if not test_email_connection():
    print("\nPlease fix the email configuration and try again.")
    exit(1)

# Start HTTP server for stop functionality
server_port = 8080
local_ip = get_local_ip()
stop_url = f"http://{local_ip}:{server_port}/stop"

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
        stop_url = None

print(f"\nMonitoring started...")
print(f"High alert threshold: ¢{high_threshold:.2f}")
print(f"Low alert threshold: ¢{low_threshold:.2f}")
print(f"Email alerts will be sent to: {', '.join(recipient_emails)}")
if stop_url:
    print(f"Stop alert URL: {stop_url}")
print(f"Press Ctrl+C to stop monitoring\n")

previous_price = None

try:
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                current_price = float(data[0]["price"])
                timestamp_ms = int(data[0]["millisUTC"])
                # Convert milliseconds to datetime without pandas
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
                
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Current price: ¢{current_price:.2f}", end="")
                
                price_changed = previous_price is not None and current_price != previous_price
                
                if current_price > high_threshold:
                    if previous_price is None or previous_price <= high_threshold or price_changed:
                        print(f" ⚠️  HIGH ALERT: Price ¢{current_price:.2f} is ABOVE threshold ¢{high_threshold:.2f}!")
                        send_email_alert("HIGH", current_price, high_threshold, previous_price, stop_url)
                    else:
                        print()
                elif current_price < low_threshold:
                    if previous_price is None or previous_price >= low_threshold or price_changed:
                        print(f" ⚠️  LOW ALERT: Price ¢{current_price:.2f} is BELOW threshold ¢{low_threshold:.2f}!")
                        send_email_alert("LOW", current_price, low_threshold, previous_price, stop_url)
                    else:
                        print()
                else:
                    print()
                
                if not emails_enabled:
                    print(f"\n   ⚠️  Email alerts have been disabled via stop button.")
                    print(f"   Restart the program to re-enable email alerts.\n")
                
                previous_price = current_price
            else:
                print("Warning: No data received from API")
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user.")
