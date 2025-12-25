from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timedelta
import pandas as pd
import os

app = FastAPI(root_path="/api")

# Robust CSV path finding
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "live_data.csv"),
    os.path.join(os.path.dirname(__file__), "live_data.csv"),
    "/var/task/live_data.csv", # Common Vercel Lambda path
    "live_data.csv"
]

DATA_PATH = None
for p in POSSIBLE_PATHS:
    if os.path.exists(p):
        DATA_PATH = p
        break

if not DATA_PATH:
    # Fallback to relative if nothing found (will likely fail later but avoids crash here)
    DATA_PATH = "live_data.csv"

@app.get("/")
def root():
    return {"status": "API Online", "message": "IoT Dashboard Backend Active"}

@app.get("/data/csv")
def get_csv():
    return FileResponse(DATA_PATH, media_type="text/csv")

@app.get("/devices")
def get_devices():
    if not os.path.exists(DATA_PATH):
        return {"devices": []}
    df = pd.read_csv(DATA_PATH)
    # Assuming 'Device_ID' is the column name after normalization or as is. 
    # Based on previous file reads, it was 'Device ID' in CSV but likely 'Device_ID' after pandas read if not normalized manually here.
    # Let's check the CSV header from previous steps: "Device ID"
    # We should normalize/strip as done in the update script or just use the raw name.
    # The API reads raw CSV.
    if "Device ID" in df.columns:
        return {"devices": list(df["Device ID"].unique())}
    return {"devices": []}

@app.get("/debug")
def debug_info():
    if not os.path.exists(DATA_PATH):
        return {"error": "live_data.csv not found", "path": DATA_PATH}
    try:
        df = pd.read_csv(DATA_PATH)
        return {
            "file_size": os.path.getsize(DATA_PATH),
            "rows": len(df),
            "columns": list(df.columns),
            "head": df.head(5).to_dict(orient="records"),
            "sample_timestamp": df.iloc[0]["Timestamp"] if "Timestamp" in df.columns and not df.empty else "N/A"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/data/json")
def get_json(device_id: str = Query(None), days: int = Query(None)):
    if not os.path.exists(DATA_PATH):
        return JSONResponse([])
    df = pd.read_csv(DATA_PATH)
    
    # Filter by Device (Handle both space and underscore versions)
    if device_id:
        if "Device_ID" in df.columns:
            df = df[df["Device_ID"] == device_id]
        elif "Device ID" in df.columns:
            df = df[df["Device ID"] == device_id]


    # Filter by Date (Days)
    if days is not None and "Timestamp" in df.columns:
        try:
            # Parse timestamp. Format in CSV is likely DD/MM/YYYY HH:MM:SS based on previous output
            # "28/09/2025 05:36:18"
            df["dt"] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors='coerce')
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df["dt"] >= cutoff_date]
            # Drop the helper column if desired, but to_dict might handle it. 
            # Better to drop it to keep response clean.
            df = df.drop(columns=["dt"])
        except Exception:
            pass # If parsing fails, ignore filter
            
    return JSONResponse(df.to_dict(orient="records"))

@app.get("/data/columns")
def get_columns():
    if not os.path.exists(DATA_PATH):
        return {"columns": []}
    df = pd.read_csv(DATA_PATH)
    return {"columns": list(df.columns)}
