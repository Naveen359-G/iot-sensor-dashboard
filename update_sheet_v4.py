#!/usr/bin/env python3
"""
Version 4+ — Multi-device monitoring + per-device charts + GitHub comment update + Telegram alerts
Added:
 - Rolling window CSVs for live use (keeps last N rows per device)
 - Monthly Parquet archival for full history
 - Generates README device chart markdown snippet and injects into README placeholder
Requirements:
 - python packages: pandas, gspread, google-auth, matplotlib, requests, pyarrow
 - service account JSON at SERVICE_ACCOUNT_FILE (created by workflow)
 - Environment variables:
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
import pyarrow as pa
import pyarrow.parquet as pq

# ========================
# CONFIGURATION
# ========================
SERVICE_ACCOUNT_FILE = "service_account.json"   # path to Google service account file (created by workflow)
SHEET_NAME = "Week 39/52"
START_ROW = 72
REMOVE_COLUMN = "eCO₂ (ppm)"

MAX_RECORDS = 200                 # keep up to 200 recent rows per device for charts/summary
ROLLING_WINDOW = 5000             # keep up to 5000 rows in live CSV per device (changeable)
ALERT_TEMP = 30.0                 # °C
ALERT_AQI = 600.0                 # AQI threshold (>= triggers alert)

# GitHub settings (from env)
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")      # e.g. "owner/repo"
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Telegram (from env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Google Sheet ID (from env)
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Paths
LIVE_DIR = "live_data"                      # small CSVs used by dashboards (committed)
ARCHIVE_DIR = "archive_parquet"             # monthly Parquet archives (committed or stored)
ASSETS_LOCAL = "assets_local"               # temp charts
GITHUB_ASSETS_PATH = "assets/iot_dashboards" # uploaded assets path in repo
README_SNIPPET = "device_charts_snippet.md" # generated snippet
README_FILE = "README.md"

# Marker for the comment so we can find & update it
MARKER = "<!-- IoT_SENSOR_DASHBOARD -->"

# ========================
# AUTHENTICATE GOOGLE SHEETS
# ========================
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise RuntimeError(f"Service account JSON not found at {SERVICE_ACCOUNT_FILE}")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# ========================
# HELPER FUNCTIONS
# ========================
def safe_name(s: str) -> str:
    """Create a filesystem-friendly, lowercase name for devices."""
    return str(s).strip().replace(" ", "-").replace("/", "-").replace("\\", "-").lower()

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
    """
    Upload or update a file to GitHub repository using Contents API.
    Returns the raw.githubusercontent URL on success, or None on failure.
    """
    api_url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = gh_headers(token)

    # Check if file already exists to obtain 'sha'
    get_resp = requests.get(api_url, headers=headers)
    data = {
        "message": commit_message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
    }
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
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

def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram bot token or chat ID not set; skipping alert")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("📨 Telegram alert sent successfully")
        else:
            print(f"⚠️ Telegram alert failed ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"⚠️ Exception sending Telegram alert: {e}")

# ========================
# LOAD SHEET DATA
# ========================
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
rows = sheet.get_all_records()
df = pd.DataFrame(rows)

# ========================
# NORMALIZE COLUMN NAMES
# ========================
# Make columns filesystem and code friendly: strip, replace spaces -> _, remove parentheses
df.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

# Standard names we will expect/use
# After normalization:
# "Temperature (°C)" -> "Temperature_°C"
# "AQI Value" -> "AQI_Value"
# "Humidity (%)" -> "Humidity_%"
# "Device ID" -> "Device_ID"
# "Device Health" -> "Device_Health"
# "AQI Status" -> "AQI_Status"

# ========================
# CLEAN & FILTER - overall sheet
# ========================
filtered_df = df.iloc[START_ROW - 2:].copy()
remove_col_normalized = REMOVE_COLUMN.replace(" ", "_").replace("(", "").replace(")", "")
if remove_col_normalized in filtered_df.columns:
    filtered_df.drop(columns=[remove_col_normalized], inplace=True)

# If 'Timestamp' exists, try parse it; else proceed
if 'Timestamp' in filtered_df.columns:
    filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce')
    filtered_df = filtered_df.sort_values(by='Timestamp', ascending=False).reset_index(drop=True)

filtered_df["Last_Updated_UTC"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def compute_alert_row(r):
    return generate_alert_text(r.get("Temperature_°C"), r.get("AQI_Value"))

filtered_df["Alert_Status"] = filtered_df.apply(compute_alert_row, axis=1)

if "Device_ID" not in filtered_df.columns:
    raise RuntimeError("Sheet does not contain 'Device_ID' column — cannot group per device.")

device_groups = filtered_df.groupby("Device_ID")
summary_rows = []
markdown_device_sections = []

# Ensure directories exist
os.makedirs(ASSETS_LOCAL, exist_ok=True)
os.makedirs(LIVE_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Keep a list for README snippet
device_id_list = []

for device, device_df in device_groups:
    # preserve full_df (before trimming) for archival
    full_df = device_df.copy().reset_index(drop=True)

    # Apply rolling window to keep live CSV small
    if len(full_df) > ROLLING_WINDOW:
        device_df = full_df.tail(ROLLING_WINDOW).reset_index(drop=True)
    else:
        device_df = full_df.copy().reset_index(drop=True)

    # Also keep MAX_RECORDS ordering for charts / summary - newest first
    device_df_for_chart = device_df.head(MAX_RECORDS).copy()

    # Save small live CSV for dashboard consumption (rolling window)
    device_key = safe_name(device)
    csv_path_live = os.path.join(LIVE_DIR, f"{device_key}.csv")
    device_df.to_csv(csv_path_live, index=False)
    print(f"✅ Saved live CSV for device -> {csv_path_live} ({len(device_df)} rows)")

    # Save per-run CSV as before (optional older name for compatibility)
    csv_name = f"live_data_{device_key}.csv"
    device_df.to_csv(csv_name, index=False)
    print(f"✅ Also saved compatibility CSV -> {csv_name}")

    # Generate small summary/preview for repo & charts (latest reading)
    latest = device_df.iloc[0]

    # Create trend chart for last up-to MAX_RECORDS (reverse for plotting left->right)
    last_n = device_df_for_chart.head(MAX_RECORDS)[["Temperature_°C", "AQI_Value"]].copy()
    last_n = last_n[::-1]  # oldest -> newest

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

    chart_local_path = os.path.join(ASSETS_LOCAL, f"{device_key}_trend.png")
    plt.savefig(chart_local_path)
    plt.close()
    print(f"📈 Chart saved locally → {chart_local_path}")

    # Upload chart to GitHub repo if token & repo provided
    chart_raw_url = None
    if GITHUB_TOKEN and GITHUB_REPO:
        try:
            with open(chart_local_path, "rb") as f:
                content_bytes = f.read()
            path_in_repo = f"{GITHUB_ASSETS_PATH}/{device_key}_trend.png"
            commit_msg = f"Update sensor_trends_{device_key}.png - {datetime.utcnow().isoformat()}"
            chart_raw_url = gh_upload_file(GITHUB_REPO, path_in_repo, content_bytes, GITHUB_TOKEN, commit_msg)
            if chart_raw_url:
                print(f"✅ Uploaded chart to repo → {chart_raw_url}")
        except Exception as e:
            print(f"⚠️ Chart upload failed for {device}: {e}")

    # Prepare displays & markdown
    temp_display = colorize_indicator(latest.get("Temperature_°C", "N/A"), ALERT_TEMP, "°C")
    hum_display = f"💧 {latest.get('Humidity_%', 'N/A')}"
    light_display = f"💡 {latest.get('Light', 'N/A')}"
    aqi_display = colorize_indicator(latest.get("AQI_Value", "N/A"), ALERT_AQI)
    aqi_status = latest.get("AQI_Status", "N/A")
    device_health = latest.get("Device_Health", "N/A")
    overall_alert = latest.get("Alert_Status", "✅ Normal")

    # Telegram alert: only when flips to 🔴 (temperature or AQI)
    if ("🔴" in temp_display) or ("🔴" in aqi_display):
        message = f"⚠️ Alert for *{device}*\nTemperature: {temp_display}\nAQI: {aqi_display}\nTime (UTC): {filtered_df['Last_Updated_UTC'].iloc[0]}"
        send_telegram_alert(message)

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

    # --- Parquet archival (monthly) ---
    try:
        month_tag = datetime.utcnow().strftime("%Y-%m")
        parquet_filename = f"{device_key}_{month_tag}.parquet"
        parquet_path = os.path.join(ARCHIVE_DIR, parquet_filename)

        # If archive exists, append (load existing, concat, drop dup by Timestamp if available)
        full_df_for_parquet = full_df.copy()
        # Ensure Timestamp column exists & parsed for deduplication
        if 'Timestamp' in full_df_for_parquet.columns:
            full_df_for_parquet['Timestamp'] = pd.to_datetime(full_df_for_parquet['Timestamp'], errors='coerce')

        if os.path.exists(parquet_path):
            try:
                existing = pd.read_parquet(parquet_path)
                combined = pd.concat([existing, full_df_for_parquet], ignore_index=True)
                # drop duplicates by Timestamp if present, else keep all
                if 'Timestamp' in combined.columns:
                    combined = combined.drop_duplicates(subset=['Timestamp'], keep='last').sort_values(by='Timestamp')
                combined.reset_index(drop=True, inplace=True)
                combined.to_parquet(parquet_path, index=False)
                print(f"🗄️ Appended to existing parquet archive → {parquet_path}")
            except Exception as e:
                # if read fails, overwrite to avoid breaking pipeline
                full_df_for_parquet.to_parquet(parquet_path, index=False)
                print(f"⚠️ Rewrote parquet archive due to error: {parquet_path} ({e})")
        else:
            # write new parquet
            full_df_for_parquet.to_parquet(parquet_path, index=False)
            print(f"🗄️ Created new parquet archive → {parquet_path}")
    except Exception as e:
        print(f"⚠️ Parquet archival failed for {device}: {e}")

    # add to device list for README snippet
    device_id_list.append({"device": device, "device_key": device_key, "chart_path": f"{GITHUB_ASSETS_PATH}/{device_key}_trend.png" if chart_raw_url else os.path.join(ASSETS_LOCAL, f"{device_key}_trend.png")})

# ========================
# WRITE summary CSV (small)
# ========================
summary_df = pd.DataFrame(summary_rows)
summary_live_path = os.path.join(LIVE_DIR, "live_data_summary.csv")
summary_df.to_csv(summary_live_path, index=False)
# also keep compatibility in root
summary_df.to_csv("live_data_summary.csv", index=False)
print(f"✅ Saved summary CSV -> {summary_live_path}")

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

# ========================
# Generate README device charts snippet & inject into README
# ========================
try:
    snippet_lines = ["## Device Trend Charts\n\n"]
    for d in device_id_list:
        display_name = d["device"]
        # use repo-relative path (uploaded) when chart_raw_url exists, else local path
        chart_rel_path = d["chart_path"]
        snippet_lines.append(f"### {display_name}\n")
        snippet_lines.append(f"![{display_name} Temperature & AQI]({chart_rel_path})\n\n")

    snippet_text = "".join(snippet_lines)
    with open(README_SNIPPET, "w") as f:
        f.write(snippet_text)
    print(f"✅ Wrote README snippet -> {README_SNIPPET}")

    # Inject into README.md at placeholder <!-- DEVICE_CHARTS_SNIPPET -->
    if os.path.exists(README_FILE):
        with open(README_FILE, "r", encoding="utf-8") as f:
            readme_content = f.read()
        if "<!-- DEVICE_CHARTS_SNIPPET -->" in readme_content:
            new_readme = readme_content.replace("<!-- DEVICE_CHARTS_SNIPPET -->", snippet_text)
            with open(README_FILE, "w", encoding="utf-8") as f:
                f.write(new_readme)
            print("🔁 Injected device charts into README.md")
        else:
            print("⚠️ Placeholder '<!-- DEVICE_CHARTS_SNIPPET -->' not found in README.md; snippet saved but not injected.")
    else:
        print("⚠️ README.md not found; snippet saved but not injected.")
except Exception as e:
    print(f"⚠️ Failed to generate or inject README snippet: {e}")

print("\nDone. Latest summary (CSV) saved, parquet archives updated, charts generated, and dashboard comment updated.")
