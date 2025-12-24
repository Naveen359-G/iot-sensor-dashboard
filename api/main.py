from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
import os

app = FastAPI(root_path="/api")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "live_data.csv")

@app.get("/")
def root():
    return {"status": "API Online", "message": "IoT Dashboard Backend Active"}

@app.get("/data/csv")
def get_csv():
    return FileResponse(DATA_PATH, media_type="text/csv")

@app.get("/data/json")
def get_json():
    df = pd.read_csv(DATA_PATH)
    return JSONResponse(df.tail(100).to_dict(orient="records"))

@app.get("/data/columns")
def get_columns():
    df = pd.read_csv(DATA_PATH)
    return {"columns": list(df.columns)}
