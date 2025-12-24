import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI(root_path="/api")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "live_data.csv")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

class IntervalUpdate(BaseModel):
    interval: int

# --- Helpers ---
def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        # Default settings
        return {"interval": 20, "last_calibrated": None}
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"interval": 20, "last_calibrated": None}

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

# --- Routes ---
@app.get("/")
def root():
    return {"status": "API Online", "message": "IoT Dashboard Backend Active"}

@app.get("/data/csv")
def get_csv():
    return FileResponse(DATA_PATH, media_type="text/csv")

@app.get("/data/json")
def get_json():
    if not os.path.exists(DATA_PATH):
        return JSONResponse([])
    df = pd.read_csv(DATA_PATH)
    return JSONResponse(df.tail(100).to_dict(orient="records"))

@app.get("/data/columns")
def get_columns():
    if not os.path.exists(DATA_PATH):
        return {"columns": []}
    df = pd.read_csv(DATA_PATH)
    return {"columns": list(df.columns)}

@app.get("/settings")
def get_settings():
    return load_settings()

@app.post("/settings")
def update_settings(update: IntervalUpdate):
    settings = load_settings()
    settings["interval"] = update.interval
    save_settings(settings)
    return settings

@app.post("/calibrate")
def calibrate_sensor():
    settings = load_settings()
    settings["last_calibrated"] = datetime.now().isoformat()
    save_settings(settings)
    return {"status": "calibrated", "timestamp": settings["last_calibrated"]}

@app.get("/status")
def get_status():
    settings = load_settings()
    interval = settings.get("interval", 20)
    
    last_captured = None
    next_capture = None
    
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            if not df.empty and "Timestamp" in df.columns:
                # Assuming Timestamp is already in a sortable format or we take the last row
                last_row = df.iloc[-1]
                last_ts_str = str(last_row["Timestamp"])
                
                # Check format, often it's YYYY-MM-DD HH:MM:SS
                # We'll try to parse it, or just pass it through if frontend handles parsing
                # But to calculate 'next', we need to parse it.
                # Let's attempt a common format or just return strings if parsing fails
                try:
                    # Adjust format to match your CSV's timestamp format
                    last_captured_dt = pd.to_datetime(last_ts_str) 
                    last_captured = last_captured_dt.isoformat()
                    
                    next_capture_dt = last_captured_dt + timedelta(minutes=interval)
                    next_capture = next_capture_dt.isoformat()
                except Exception:
                    last_captured = last_ts_str # Fallback
        except Exception as e:
            print(f"Error reading timestamp: {e}")

    return {
        "last_captured": last_captured,
        "next_capture": next_capture,
        "interval": interval,
        "last_calibrated": settings.get("last_calibrated")
    }
