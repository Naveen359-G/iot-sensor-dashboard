#!/usr/bin/env python3
"""
Version 4 — Multi-device monitoring + per-device charts + GitHub comment update + Telegram alerts
Requirements:
 - python packages: pandas, gspread, google-auth, matplotlib, requests
 - service account JSON at SERVICE_ACCOUNT_FILE
 - Environment variables (recommended):
     GOOGLE_SHEET_ID
     TELEGRAM_BOT_TOKEN
     TELEGRAM_CHAT_ID
     GITHUB_REPOSITORY (owner/repo)
     ISSUE_NUMBER (issue to post/update; default "1")
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
# CONFIGURATION
# ========================
SERVICE_ACCOUNT_FILE = "service_account.json"   # path to Google service account file
SHEET_NAME = "Week 39/52"
START_ROW = 72
REMOVE_COLUMN = "eCO₂ (ppm)"

MAX_RECORDS = 200                 # limit per device
ALERT_TEMP = 30.0                 # °C
ALERT_AQI = 600.0                 # AQI threshold (>= triggers alert)

# GitHub settings (from env)
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")      # e.g. "Naveen359-G/iot-sensor-dashboard"
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Telegram alerts (from env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Where to store images in repo (path inside repo)
GITHUB_ASSETS_PATH = "assets/iot_dashboards"      # will create/update files here

# Marker for the comment so we can find & update it
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

def gh_headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def gh_upload_file(repo, path_in_repo, content_bytes, token, commit_message="Add asset"):
    api_url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = gh_headers(token)

    # Check if file already exists
    get_resp = requests.get(api_url, headers=headers)
    data = {
        "message": commit_message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
    }
    if get_resp.status_code == 200:
        get_json = get_resp.json()
        sha = get_json.get("sha")
        data["sha"] = sha

    put_resp = requests.put(api_url, headers=headers, json=data)
    if put_resp.status_code in (200, 201):
        branch_guess = "main"
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch_guess}/{path_in_repo}"
        return raw_url
    else:
        print(f"⚠️ Failed to upload {path_in_repo} to GitHub ({put_resp.status_code}): {put_resp.text}")
        return None

def find_existing_dashboard_comment(repo, issue_number, token):
    base_comments_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    r = requests.get(base_comments_url, headers=gh_headers(token))
    if r.status_code != 200:
        print(f"⚠️ Failed to list issue comments ({r.status_code}): {r.text}")
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
        if r.status_code == 200:
            print("🔄 Updated existing GitHub dashboard comment successfully.")
            return True
        else:
            print(f"⚠️ Failed to update comment ({r.status_code}): {r.text}")
            return False
    else:
        post_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        r = requests.post(post_url, headers=gh_headers(token), json={"body": body_md})
        if r.status_code == 201:
            print("💬 Created new dashboard comment on GitHub.")
            return True
        else:
            print(f"⚠️ Failed to create comment ({r.status_code}): {r.text}")
            return False

# ========================
# TELEGRAM ALERT FUNCTION
# ========================
def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ Telegram alert failed: {e}")

# ========================
# LOAD SHEET DATA
# ========================
sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"]).worksheet(SHEET_NAME)
rows = sheet.get_all_records()
df = pd.DataFrame(rows)

# ========================
# NORMALIZE COLUMN NAMES
# ========================
df.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

# ========================
# CLEAN & FILTER
# ========================
filtered_df = df.iloc[START_ROW - 2:].copy()
if REMOVE_COLUMN.replace(" ", "_").replace("(", "").replace(")", "") in filtered_df.columns:
    filtered_df.drop(columns=[REMOVE_COLUMN.replace(" ", "_").replace("(", "").replace(")", "")], inplace=True)

if "Timestamp" in filtered_df.columns:
    filtered_df = filtered_df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)

filtered_df["Last_Updated_UTC"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def compute_alert_row(r):
    return generate_alert_text(r.get("Temperature_°C"), r.get("AQI_Value"))

filtered_df["Alert_Status"] = filtered_df.apply(compute_alert_row, axis=1)

if "Device_ID" not in filtered_df.columns:
    raise RuntimeError("Sheet does not contain 'Device_ID' column — cannot group per device.")

device_groups = filtered_df.groupby("Device_ID")
summary_rows = []
markdown_device_sections = []

os.makedirs("assets_local", exist_ok=True)

for device, device_df in device_groups:
    device_df = device_df.head(MAX_RECORDS).copy()

    csv_name = f"live_data_{device}.csv"
    device_df.to_csv(csv_name, index=False)
    print(f"✅ Saved {csv_name} ({len(device_df)} records)")

    latest = device_df.iloc[0]
    last_n = device_df.head(10)[["Temperature_°C", "AQI_Value"]].copy()[::-1]

    plt.figure(figsize=(6, 3))
    if "Temperature_°C" in last_n.columns:
        plt.plot(last_n["Temperature_°C"].values, marker="o", label="Temperature (°C)")
    if "AQI_Value" in last_n.columns:
        plt.plot(last_n["AQI_Value"].values, marker="s", label="AQI Value")
    plt.title(f"{device} - Recent Trends (Last {len(last_n)} Readings)")
    plt.xlabel("Reading Index (older → newer)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    chart_local_path = os.path.join("assets_local", f"sensor_trends_{device}.png")
    plt.savefig(chart_local_path)
    plt.close()
    print(f"📈 Chart saved locally → {chart_local_path}")

    chart_raw_url = None
    if GITHUB_TOKEN and GITHUB_REPO:
        with open(chart_local_path, "rb") as f:
            content_bytes = f.read()
        path_in_repo = f"{GITHUB_ASSETS_PATH}/sensor_trends_{device}.png"
        commit_msg = f"Update sensor_trends_{device}.png - {datetime.utcnow().isoformat()}"
        chart_raw_url = gh_upload_file(GITHUB_REPO, path_in_repo, content_bytes, GITHUB_TOKEN, commit_msg)
        if chart_raw_url:
            print(f"✅ Uploaded chart to repo → {chart_raw_url}")

    temp_display = colorize_indicator(latest.get("Temperature_°C", "N/A"), ALERT_TEMP, "°C")
    hum_display = f"💧 {latest.get('Humidity_%', 'N/A')}"
    light_display = f"💡 {latest.get('Light', 'N/A')}"
    aqi_display = colorize_indicator(latest.get("AQI_Value", "N/A"), ALERT_AQI)
    aqi_status = latest.get("AQI_Status", "N/A")
    device_health = latest.get("Device_Health", "N/A")
    overall_alert = latest.get("Alert_Status", "✅ Normal")

    # Send Telegram alert only if it flips to 🔴
    if "🔴" in temp_display or "🔴" in aqi_display:
        send_telegram_alert(f"⚠️ Alert for {device}: {overall_alert}")

    chart_md = f"![Sensor Trends]({chart_raw_url})" if chart_raw_url else f"![Sensor Trends](./{chart_local_path})"

    device_section = f"""
<details>
<summary>🧠 **{device}** — {overall_alert}</summary>

_Last updated (UTC): **{filtered_df['Last_Updated_UTC'].iloc[0]}**_

| Metric | Value | Status |
|:-------|:------|:-------|
| Temperature | {temp_display} | {'⚠️ Alert' if '🔴' in temp_display else '✅ Normal'} |
| Humidity | {hum_display} | ✅ Normal |
| Light | {light_display} | ✅ Normal |
| AQI | {aqi_display} | {'⚠️ Alert' if '🔴' in aqi_display else '✅ Normal'} |
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
        "Temperature (°C)": latest.get("Temperature_°C"),
        "Humidity (%)": latest.get("Humidity_%"),
        "Light": latest.get("Light"),
        "AQI Value": latest.get("AQI_Value"),
        "Alert": overall_alert
    })

# ========================
# WRITE summary CSV
# ========================
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("live_data_summary.csv", index=False)
print("✅ Saved live_data_summary.csv")

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
# POST or UPDATE GITHUB ISSUE COMMENT
# ========================
if GITHUB_TOKEN and GITHUB_REPO:
    ok = update_or_create_issue_comment(GITHUB_REPO, ISSUE_NUMBER, GITHUB_TOKEN, dashboard_md)
    if not ok:
        print("⚠️ Posting/updating dashboard comment failed.")
else:
    print("\n⚠️ GitHub environment variables not found. Printing dashboard markdown below:\n")
    print(dashboard_md)

print("\nDone. Latest summary (CSV) saved and dashboard generated.")
