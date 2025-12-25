from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timedelta
import pandas as pd
import os
import urllib.request
from io import StringIO

app = FastAPI(root_path="/api")

# Robust CSV path finding
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "live_data.csv"),
    os.path.join(os.path.dirname(__file__), "live_data.csv"),
    "/var/task/live_data.csv",
    "live_data.csv"
]

DATA_PATH = None
for p in POSSIBLE_PATHS:
    if os.path.exists(p):
        DATA_PATH = p
        break
if not DATA_PATH:
    DATA_PATH = "live_data.csv"

# GitHub Repository for fallbacks
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY") or "Naveen359-G/iot-sensor-dashboard"

# Google Sheets Live Export URL
SHEET_ID = "1EZXrkYyfK-QTrLAlf9-mSelOcmbFCaxzPWYaHHcZbdE"
SHEET_NAME = "Week 39/52"
GS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME.replace(' ', '%20')}"

def clean_df(df, is_live_sheet=False):
    """Normalize column names and filter data based on Kaggle/Project requirements."""
    # 1. Row filtering (Skip first 71 rows from live sheet as per Kaggle logic)
    if is_live_sheet and len(df) > 71:
        df = df.iloc[71:].reset_index(drop=True)
    
    # 2. Normalize column names
    df.columns = [str(c).strip().replace(' ', '_').replace('(', '').replace(')', '').replace('°C', 'C') for c in df.columns]
    
    # 3. Drop unwanted columns (eCO2/CO2 versions)
    cols_to_drop = [col for col in df.columns if any(x in col for x in ['eCO', 'CO2', 'eCO\u2082'])]
    df = df.drop(columns=cols_to_drop, errors='ignore')
    
    # 4. Limit to latest 1000 records
    if len(df) > 1000:
        df = df.tail(1000)
    
    return df

def get_df():
    """Fetch DataFrame: Google Sheets (Primary) -> GitHub Raw (Fallback) -> Local (Emergency)."""
    # 1. Try Google Sheets Direct
    try:
        req = urllib.request.Request(GS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                df = pd.read_csv(StringIO(content))
                df = clean_df(df, is_live_sheet=True)
                df["_source"] = "Google Sheets (Live)"
                return df
    except Exception as e:
        print(f"⚠️ Google Sheets fetch failed: {e}")

    # 2. Try GitHub Raw Fallback
    timestamp = int(datetime.now().timestamp() // 60)
    live_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/live_data.csv?v={timestamp}"
    try:
        req = urllib.request.Request(live_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                df = pd.read_csv(StringIO(content))
                df = clean_df(df, is_live_sheet=False)
                df["_source"] = "GitHub (Live Fallback)"
                return df
    except Exception as e:
        print(f"⚠️ GitHub Raw fetch failed: {e}")
    
    # 3. Try Local Emergency Fallback
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            df = clean_df(df, is_live_sheet=False)
            df["_source"] = "Local (Emergency Fallback)"
            return df
        except Exception:
            pass
    return None

@app.get("/")
def root():
    df = get_df()
    source = df["_source"].iloc[0] if df is not None and "_source" in df.columns else "Unknown"
    return {"status": "API Online", "source": source, "repo": GITHUB_REPO}


@app.get("/data/csv")
def get_csv():
    # Still returns the deploy-time CSV for download
    return FileResponse(DATA_PATH, media_type="text/csv")

@app.get("/devices")
def get_devices():
    df = get_df()
    if df is None:
        return {"devices": []}
    try:
        device_col = next((c for c in df.columns if "device" in c.lower()), None)
        if device_col:
            return {"devices": sorted([str(d).strip() for d in df[device_col].dropna().unique()])}
    except Exception:
        pass
    return {"devices": []}

@app.get("/debug")
def debug_info():
    df = get_df()
    source = df["_source"].iloc[0] if df is not None and "_source" in df.columns else "None (Fetch Failed)"
    return {
        "status": "API Online",
        "data_source": source,
        "repo": GITHUB_REPO,
        "rows": len(df) if df is not None else 0,
        "columns": list(df.columns) if df is not None else []
    }


@app.get("/data/json")
def get_json(device_id: str = Query(None), days: int = Query(None)):
    df = get_df()
    if df is None:
        return JSONResponse([])
    
    # Filter by Device (Extreme Robust)
    if device_id:
        device_col = next((c for c in df.columns if "device" in c.lower()), None)
        if device_col:
            target = str(device_id).lower().replace("_", "-").strip()
            df = df[df[device_col].astype(str).str.lower().str.replace("_", "-").str.strip() == target]

    # Filter by Date
    if days is not None and "Timestamp" in df.columns:
        try:
            df["dt"] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors='coerce')
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df["dt"] >= cutoff_date].copy()
            df = df.drop(columns=["dt"])
        except Exception:
            pass
            
    return JSONResponse(df.to_dict(orient="records"))

@app.get("/data/columns")
def get_columns():
    df = get_df()
    if df is None:
        return {"columns": []}
    return {"columns": list(df.columns)}
