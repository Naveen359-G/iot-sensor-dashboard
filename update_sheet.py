#!/usr/bin/env python3
"""
Version 4 — Multi-device monitoring + per-device charts + GitHub comment update + Telegram alerts
Requirements:
 - python packages: pandas, gspread, google-auth, matplotlib, requests
 - service account JSON at SERVICE_ACCOUNT_FILE
 - Environment variables (required):
     GOOGLE_SHEET_ID
     TELEGRAM_BOT_TOKEN
     TELEGRAM_CHAT_ID
     GITHUB_REPOSITORY
     ISSUE_NUMBER
     GITHUB_TOKEN
"""

import os
import base64
import json
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import requests

# ========================
# CONFIGURATION FROM ENV
# ========================
SERVICE_ACCOUNT_FILE = "service_account.json"

SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")
if not SPREADSHEET_ID:
    raise RuntimeError("GOOGLE_SHEET_ID environment variable not set")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")      # e.g., "owner/repo"
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SHEET_NAME = "Week 39/52"
START_ROW = 72
REMOVE_COLUMN = "eCO₂ (ppm)"

MAX_RECORDS = 200                 # limit per device
ALERT_TEMP = 30.0                 # °C
ALERT_AQI = 600.0                 # AQI threshold (>= triggers alert)

GITHUB_ASSETS_PATH = "assets/iot_dashboards"
MARKER = "<!-- IoT_SENSOR_DASHBOARD -->"

# ========================
# AUTHENTICATE GOOGLE SHEETS
# ========================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# ========================
# HELPER FUNCTIONS
# ========================
def colorize_indicator(value, threshold, unit=""):
    try:
        val = float(value)
    except Exception:
        return f"🔸 {value}{unit}"
    if val >= threshold:
        return f"🔴 **{val}{unit}**"
    elif val >= threshold * 0.8:
        return f"🟠 {val}{unit}"
    else:
        return f"🟢 {val}{unit}"

def generate_alert_text(temp, aqi):
    alerts = []
    try:
        if float(temp) > ALERT_TEMP:
            alerts.append("🌡️ High Temp")
    except Exception:
        pass
    try:
        if float(aqi) >= ALERT_AQI:
            alerts.append("🌫️ High AQI")
    except Exception:
        pass
    return " | ".join(alerts) if alerts else "✅ Normal"

def send_telegram_alert(message: str):
    """Send Telegram message (only if bot token and chat ID set)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram bot or chat ID not configured. Skipping alert.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("📩 Telegram alert sent successfully.")
        else:
            print(f"⚠️ Telegram alert failed: {r.text}")
    except Exception as e:
        print(f"⚠️ Exception sending Telegram alert: {e}")

# ========================
# LOAD SHEET DATA
# ========================
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
rows = sheet.get_all_records()
df = pd.DataFrame(rows)

# ========================
# CLEAN & FILTER
# ========================
filtered_df = df.iloc[START_ROW - 2:].copy()
if REMOVE_COLUMN in filtered_df.columns:
    filtered_df.drop(columns=[REMOVE_COLUMN], inplace=True)

if "Timestamp" in filtered_df.columns:
    filtered_df = filtered_df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)

filtered_df["Last_Updated_UTC"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def compute_alert_row(r):
    return generate_alert_text(r.get("Temperature (°C)"), r.get("AQI Value"))

filtered_df["Alert_Status"] = filtered_df.apply(compute_alert_row, axis=1)

if "Device ID" not in filtered_df.columns:
    raise RuntimeError("Sheet does not contain 'Device ID' column — cannot group per device.")

device_groups = filtered_df.groupby("Device ID")
summary_rows = []
markdown_device_sections = []

os.makedirs("assets_local", exist_ok=True)

# ========================
# PROCESS DEVICES
# ========================
for device, device_df in device_groups:
    device_df = device_df.head(MAX_RECORDS).copy()
    csv_name = f"live_data_{device}.csv"
    device_df.to_csv(csv_name, index=False)
    print(f"✅ Saved {csv_name} ({len(device_df)} records)")

    latest = device_df.iloc[0]

    # Generate trend chart
    last_n = device_df.head(10)[["Temperature (°C)", "AQI Value"]].copy()[::-1]
    plt.figure(figsize=(6, 3))
    if "Temperature (°C)" in last_n.columns:
        plt.plot(last_n["Temperature (°C)"].values, marker="o", label="Temperature (°C)")
    if "AQI Value" in last_n.columns:
        plt.plot(last_n["AQI Value"].values, marker="s", label="AQI Value")
    plt.title(f"{device} - Recent Trends (Last {len(last_n)} Readings)")
    plt.xlabel("Reading Index (older → newer)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    chart_local_path = os.path.join("assets_local", f"sensor_trends_{device}.png")
    plt.savefig(chart_local_path)
    plt.close()

    # ALERT: Send Telegram if device turns 🔴
    if "Temperature (°C)" in latest and float(latest["Temperature (°C)"]) > ALERT_TEMP:
        alert_msg = f"⚠️ *{device}* temperature alert: {latest['Temperature (°C)']}°C (exceeds {ALERT_TEMP})"
        send_telegram_alert(alert_msg)
    if "AQI Value" in latest and float(latest["AQI Value"]) >= ALERT_AQI:
        alert_msg = f"⚠️ *{device}* AQI alert: {latest['AQI Value']} (exceeds {ALERT_AQI})"
        send_telegram_alert(alert_msg)

    # prepare markdown for GitHub issue
    temp_display = colorize_indicator(latest.get("Temperature (°C)", "N/A"), ALERT_TEMP, "°C")
    hum_display = f"💧 {latest.get('Humidity (%)', 'N/A')}"
    light_display = f"💡 {latest.get('Light', 'N/A')}"
    aqi_display = colorize_indicator(latest.get("AQI Value", "N/A"), ALERT_AQI)
    aqi_status = latest.get("AQI Status", "N/A")
    device_health = latest.get("Device Health", "N/A")
    overall_alert = latest.get("Alert_Status", "✅ Normal")

    chart_md = f"![Sensor Trends](./{chart_local_path})"
    device_section = f"""
<details>
<summary>🧠 **{device}** — {overall_alert}</summary>

_Last updated (UTC): **{filtered_df['Last_Updated_UTC'].iloc[0]}**_

| Metric | Value | Status |
|:-------|:------|:-------|
| Temperature | {temp_display} | {'⚠️ Alert' if str(latest.get('Temperature (°C)', '')) != 'N/A' and float(latest.get('Temperature (°C)', 0)) > ALERT_TEMP else '✅ Normal'} |
| Humidity | {hum_display} | ✅ Normal |
| Light | {light_display} | ✅ Normal |
| AQI | {aqi_display} | {'⚠️ Alert' if str(latest.get('AQI Value', '')) != 'N/A' and float(latest.get('AQI Value', 0)) >= ALERT_AQI else '✅ Normal'} |
| AQI Status | 🌫️ {aqi_status} |  |
| Device Health | ⚙️ {device_health} |  |
| Overall Alert | {overall_alert} |  |

#### 📊 Trend (Last readings)
{chart_md}

</details>
"""
    markdown_device_sections.append(device_section)
    summary_rows.append({
        "Device": device,
        "Temperature (°C)": latest.get("Temperature (°C)"),
        "Humidity (%)": latest.get("Humidity (%)"),
        "Light": latest.get("Light"),
        "AQI Value": latest.get("AQI Value"),
        "Alert": overall_alert
    })

# ========================
# WRITE SUMMARY CSV
# ========================
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("live_data_summary.csv", index=False)

# ========================
# BUILD DASHBOARD MARKDOWN
# ========================
dashboard_md = f"""{MARKER}

# 🌡️ IoT Sensor Monitoring Dashboard

_Last update (UTC): **{filtered_df['Last_Updated_UTC'].iloc[0]}**_

**Devices monitored:** {len(summary_rows)}

---

{"".join(markdown_device_sections)}

---

_This comment is auto-generated by the IoT monitoring script._
"""

# ========================
# POST OR UPDATE GITHUB ISSUE COMMENT
# ========================
def gh_headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def find_existing_dashboard_comment(repo, issue_number, token):
    base_comments_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    r = requests.get(base_comments_url, headers=gh_headers(token))
    if r.status_code != 200:
        return None
    for comment in r.json():
        if MARKER in (comment.get("body") or ""):
            return comment.get("id")
    return None

def update_or_create_issue_comment(repo, issue_number, token, body_md):
    comment_id = find_existing_dashboard_comment(repo, issue_number, token)
    if comment_id:
        patch_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        r = requests.patch(patch_url, headers=gh_headers(token), json={"body": body_md})
        return r.status_code == 200
    else:
        post_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        r = requests.post(post_url, headers=gh_headers(token), json={"body": body_md})
        return r.status_code == 201

if GITHUB_TOKEN and GITHUB_REPO:
    update_or_create_issue_comment(GITHUB_REPO, ISSUE_NUMBER, GITHUB_TOKEN, dashboard_md)
else:
    print(dashboard_md)

print("✅ Done. Latest summary CSV and dashboard generated.")
