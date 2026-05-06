import requests
import pandas as pd
import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = "https://hourlypricing.comed.com/api?type=currenthouraverage"

# -------------------------
# LOAD CONFIG
# -------------------------
with open("config.json", "r") as f:
    config = json.load(f)

HIGH = float(config["high"])
LOW = float(config["low"])
ENABLED = config.get("enabled", True)

# -------------------------
# LOAD LAST STATE (prevents spam)
# -------------------------
STATE_FILE = "last_state.json"

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"last_price": None, "last_alert": None}

last_price = state.get("last_price")
last_alert = state.get("last_alert")

# -------------------------
# EMAIL SETUP
# -------------------------
SENDER = os.getenv("SENDER")
PASSWORD = os.getenv("PASSWORD")
RECIPIENT = os.getenv("EMAIL")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER, PASSWORD)
    server.sendmail(SENDER, RECIPIENT, msg.as_string())
    server.quit()

# -------------------------
# GET CURRENT PRICE
# -------------------------
response = requests.get(URL)
data = response.json()

if not data:
    print("No data")
    exit()

price = float(data[0]["price"])
timestamp = pd.to_datetime(int(data[0]["millisUTC"]), unit="ms")

print(f"[{timestamp}] Price: ¢{price:.2f}")

# -------------------------
# DETECT CHANGE
# -------------------------
price_changed = (last_price is None) or (price != last_price)

alert_type = None

if price > HIGH:
    alert_type = "HIGH"
elif price < LOW:
    alert_type = "LOW"

# -------------------------
# SEND ONLY IF:
# - price changed
# - AND new alert condition
# - AND not same as last alert
# -------------------------
if ENABLED and price_changed and alert_type != last_alert:

    if alert_type == "HIGH":
        send_email(
            "HIGH PRICE ALERT",
            f"Price crossed HIGH threshold\n\nPrice: ¢{price:.2f}\nThreshold: ¢{HIGH}"
        )

    elif alert_type == "LOW":
        send_email(
            "LOW PRICE ALERT",
            f"Price crossed LOW threshold\n\nPrice: ¢{price:.2f}\nThreshold: ¢{LOW}"
        )

    # update last alert
    last_alert = alert_type

# -------------------------
# SAVE STATE
# -------------------------
with open(STATE_FILE, "w") as f:
    json.dump({
        "last_price": price,
        "last_alert": last_alert
    }, f)
