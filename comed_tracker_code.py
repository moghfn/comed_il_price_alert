import requests
import pandas as pd
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

url = "https://hourlypricing.comed.com/api?type=currenthouraverage"

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

def send_email_alert(alert_type, current_price, threshold):
    """Send an email alert when price threshold is crossed."""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        if alert_type == "HIGH":
            msg['Subject'] = f"⚠️ HIGH PRICE ALERT - ${current_price:.2f}"
            body = f"""
Price Alert Notification

ALERT TYPE: HIGH PRICE ALERT

Current Price: ${current_price:.2f}
Threshold: ${threshold:.2f}

The electricity price has exceeded your high threshold of ${threshold:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your price monitoring system.
"""
        else:  # LOW
            msg['Subject'] = f"⚠️ LOW PRICE ALERT - ${current_price:.2f}"
            body = f"""
Price Alert Notification

ALERT TYPE: LOW PRICE ALERT

Current Price: ${current_price:.2f}
Threshold: ${threshold:.2f}

The electricity price has dropped below your low threshold of ${threshold:.2f}.

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your price monitoring system.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
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

print(f"\nMonitoring started...")
print(f"High alert threshold: ${high_threshold:.2f}")
print(f"Low alert threshold: ${low_threshold:.2f}")
print(f"Email alerts will be sent to: {recipient_email}")
print(f"Press Ctrl+C to stop monitoring\n")

# Track previous price to avoid duplicate alerts
previous_price = None
high_alert_triggered = False
low_alert_triggered = False

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
                
                # Check high threshold
                if current_price > high_threshold:
                    if not high_alert_triggered or previous_price is None or previous_price <= high_threshold:
                        print(f" ⚠️  HIGH ALERT: Price ${current_price:.2f} is ABOVE threshold ${high_threshold:.2f}!")
                        send_email_alert("HIGH", current_price, high_threshold)
                        high_alert_triggered = True
                    else:
                        print()
                # Check low threshold
                elif current_price < low_threshold:
                    if not low_alert_triggered or previous_price is None or previous_price >= low_threshold:
                        print(f" ⚠️  LOW ALERT: Price ${current_price:.2f} is BELOW threshold ${low_threshold:.2f}!")
                        send_email_alert("LOW", current_price, low_threshold)
                        low_alert_triggered = True
                    else:
                        print()
                else:
                    print()
                    # Reset alert flags when price returns to normal range
                    if previous_price is not None:
                        if previous_price > high_threshold and current_price <= high_threshold:
                            high_alert_triggered = False
                            print(f"   ✓ Price has returned below high threshold")
                        if previous_price < low_threshold and current_price >= low_threshold:
                            low_alert_triggered = False
                            print(f"   ✓ Price has returned above low threshold")
                
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