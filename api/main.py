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

# GitHub Live Data URL (Hardcoded fallback for reliability)
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY") or "Naveen359-G/iot-sensor-dashboard"

def get_df():
    """Fetch DataFrame from GitHub Raw if possible, otherwise local file."""
    # Add a cache-busting query parameter (?v=) to ensure we get newest data from GitHub CDN
    timestamp = int(datetime.now().timestamp() // 60) # updates every minute
    live_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/live_data.csv?v={timestamp}"
    
    try:
        with urllib.request.urlopen(live_url, timeout=5) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                df = pd.read_csv(StringIO(content))
                print(f"✅ Fetched live data from GitHub: {len(df)} rows")
                return df
    except Exception as e:
        print(f"⚠️ GitHub Raw fetch failed, falling back to local: {e}")
    
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    return None


@app.get("/")
def root():
    return {"status": "API Online", "message": "IoT Dashboard Backend Active", "live_sync": GITHUB_RAW_URL is not None}

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
    return {
        "source": "GitHub Raw" if GITHUB_RAW_URL else "Local Filesystem",
        "raw_url": GITHUB_RAW_URL,
        "exists": df is not None,
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
