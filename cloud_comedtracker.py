import requests
import pandas as pd
import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

url = "https://hourlypricing.comed.com/api?type=currenthouraverage"

# Load config (thresholds)
with open("config.json", "r") as f:
    config = json.load(f)

high_threshold = float(config["upper"])
low_threshold = float(config["lower"])

if low_threshold >= high_threshold:
    raise ValueError("Lower threshold must be less than upper threshold.")

# Environment variables (from GitHub Secrets)
sender_email = os.getenv("SENDER")
sender_password = os.getenv("PASSWORD")
recipient_email = os.getenv("EMAIL")

smtp_server = "smtp.gmail.com"
smtp_port = 587

def send_email(alert_type, current_price, threshold):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email

    if alert_type == "HIGH":
        msg['Subject'] = f"⚠️ HIGH PRICE ALERT - ${current_price:.2f}"
        body = f"Price is HIGH: ${current_price:.2f} (threshold: ${threshold:.2f})"
    else:
        msg['Subject'] = f"⚠️ LOW PRICE ALERT - ${current_price:.2f}"
        body = f"Price is LOW: ${current_price:.2f} (threshold: ${threshold:.2f})"

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()

# Fetch price
response = requests.get(url)
response.raise_for_status()
data = response.json()

if data:
    current_price = float(data[0]["price"])
    timestamp_ms = int(data[0]["millisUTC"])
    timestamp = pd.to_datetime(timestamp_ms, unit="ms")

    print(f"[{timestamp}] Price: ${current_price:.2f}")

    if current_price > high_threshold:
        send_email("HIGH", current_price, high_threshold)

    elif current_price < low_threshold:
        send_email("LOW", current_price, low_threshold)

else:
    print("No data received")