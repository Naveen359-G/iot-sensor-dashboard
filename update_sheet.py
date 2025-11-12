import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

# -----------------------
# Config - change only if needed
# -----------------------
SPREADSHEET_ID = "1EZXrkYyfK-QTrLAlf9-mSelOcmbFCaxzPWYaHHcZbdE"
SHEET_NAME = "Week 39/52"
OUTPUT_FILE = "live_data.csv"
SERVICE_ACCOUNT_FILE = "service_account.json"  # created from secret in the github workflow

# -----------------------
# Authenticate & read sheet
# -----------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

sh = client.open_by_key(SPREADSHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)
rows = worksheet.get_all_records()

df = pd.DataFrame(rows)

# -----------------------
# Filter: skip first 71 rows (start from row 72) and drop eCO₂ (ppm)
# -----------------------
df = df.iloc[71:].copy()
if "eCO₂ (ppm)" in df.columns:
    df = df.drop(columns=["eCO₂ (ppm)"])

# Normalize column names
df.columns = [c.strip().replace(" ", "_") for c in df.columns]
df.dropna(how="all", inplace=True)

# Add a generation timestamp column (optional — helpful for debugging)
df["_exported_at_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# Save CSV
df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ {OUTPUT_FILE} updated: {df.shape[0]} rows, {df.shape[1]} columns")
