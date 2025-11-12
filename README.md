This **README.md** version includes placeholders for per-device charts, making it visually appealing and ready for GitHub:

```markdown
# IoT Sensor Monitoring & Automated Alert System

## Overview
This repository implements an end-to-end **IoT sensor monitoring system** with automated alerts and visualization. It tracks environmental parameters such as temperature, humidity, light intensity, and air quality (AQI) for multiple devices. Data is sourced from Google Sheets, analyzed, visualized, and automatically updated in GitHub. Alerts are generated when sensor readings exceed defined thresholds.  

**Key features:**  
- Multi-device monitoring  
- Automated CSV updates and per-device charts  
- GitHub issue comment dashboard  
- IoT sensor alert template for automatic issue creation  
- Configurable alert thresholds (temperature and AQI)  
- Optional Telegram notifications  

---

## File & Folder Structure

iot-sensor-dashboard/
│
├── update_sheet_v4.py          # Main Python script for reading, processing, and updating sensor data
├── README.md                   # Project documentation
├── ALERT_ISSUE_TEMPLATE.md     # Template for GitHub issue alerts
├── requirements.txt            # Python dependencies
├── assets_local/               # Temporary local folder for charts
├── assets/iot_dashboards/      # Repository folder for uploaded charts
└── .github/
└── workflows/
└── update_live_data.yml # GitHub Actions workflow

```

iot-sensor-dashboard/
│
├── update_sheet_v4.py          # Main Python script for reading, processing, and updating sensor data
├── README.md                   # Project documentation
├── ALERT_ISSUE_TEMPLATE.md     # Template for GitHub issue alerts
├── requirements.txt            # Python dependencies
├── assets_local/               # Temporary local folder for charts
├── assets/iot_dashboards/      # Repository folder for uploaded charts
└── .github/
└── workflows/
└── update_live_data.yml # GitHub Actions workflow

````

---

## Step 1: Data Collection

1. **IoT Devices:** Two devices (`indoor-farm-01` and `indoor-farm-02`) collect environmental data.  
2. **Google Sheets:** Sensor readings are logged, including:  
   - `Timestamp`  
   - `Device ID`  
   - `Temperature (°C)`  
   - `Humidity (%)`  
   - `Light`  
   - `AQI Value`  
   - `AQI Status`  
   - `Device Health`  
3. **Historical Analysis:** Initial exploration via Kaggle notebooks:  
   - Cleaning missing or erroneous data  
   - Visualizing trends (temperature, AQI)  
   - Identifying thresholds for alerts  

---

## Step 2: Data Processing Script (`update_sheet_v4.py`)

**Purpose:** Reads Google Sheet data, processes it, generates per-device CSVs and trend charts, and updates GitHub.  

**Key features:**  
- **Google Sheets Authentication:** Service account JSON stored as GitHub secret  
- **Data Cleaning & Filtering:** Keeps only latest `MAX_RECORDS` per device  
- **Alert Computation:**  
  - Temperature > 30°C → 🔴 alert  
  - AQI ≥ 600 → 🔴 alert  
- **Visualization:** Trend charts for last 10 readings per device (charts saved under `assets/iot_dashboards/`)  
- **CSV Output:**  
  - `live_data_<device>.csv` → per-device data  
  - `live_data_summary.csv` → summary of all devices  
- **GitHub Integration:**  
  - Uploads charts to `assets/iot_dashboards/`  
  - Updates GitHub issue comment dashboard  
- **Telegram Alerts (Optional):** Sent only when a device flips to 🔴.  

---

## Step 3: GitHub Actions Workflow (`update_live_data.yml`)

**Purpose:** Automates the execution of `update_sheet_v4.py` and updates CSVs and dashboards in GitHub.  

**Workflow:**  
- **Triggers:**  
  - Hourly via cron  
  - Manual trigger via `workflow_dispatch`  
- **Jobs:**  
  1. Checkout repository  
  2. Set up Python 3.11  
  3. Install dependencies (`pandas`, `gspread`, `google-auth`, `matplotlib`, `requests`)  
  4. Create service account JSON from secret  
  5. Run `update_sheet_v4.py`  
  6. Commit & push updated CSVs if changes exist  

**Secrets used:**  

| Secret Name               | Description                                         |
|---------------------------|-----------------------------------------------------|
| `GOOGLE_SHEET_ID`          | Google Sheet ID containing sensor data            |
| `TELEGRAM_BOT_TOKEN`       | Telegram bot token for alerts                      |
| `TELEGRAM_CHAT_ID`         | Telegram chat ID for alerts                        |
| `GITHUB_REPOSITORY`        | Owner/repo (e.g., `Naveen359-G/iot-sensor-dashboard`) |
| `ISSUE_NUMBER`             | GitHub issue number to post dashboards/comments   |
| `GITHUB_TOKEN`             | Workflow token or personal token                  |

---

## Step 4: Alert System

**GitHub Issue Template (`ALERT_ISSUE_TEMPLATE.md`):**  
- Automatically creates issues when thresholds are exceeded  
- Fields include device name, timestamp, alert type, sensor readings, thresholds, and suggested actions  
- Enables rapid investigation of high temperature or poor AQI  

---

## Step 5: Visualization

Per-device trend charts are generated and uploaded to GitHub:  

### Indoor Farm 01
![Indoor Farm 01 Temperature & AQI](assets/iot_dashboards/indoor-farm-01_trend.png)

### Indoor Farm 02
![Indoor Farm 02 Temperature & AQI](assets/iot_dashboards/indoor-farm-02_trend.png)

**Notes:**  
- Charts include last 10 readings for temperature and AQI  
- 🔴 alerts are highlighted on charts  
- File names: `assets/iot_dashboards/<device>_trend.png`  

---

## Step 6: Security & Secrets

- All sensitive information is stored in **GitHub secrets**  
- Ensures credentials are **never exposed publicly**  

---

## Step 7: Usage Instructions

1. Clone the repository:
```bash
git clone https://github.com/<owner>/iot-sensor-dashboard.git
cd iot-sensor-dashboard
````

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up GitHub secrets:

   * `GOOGLE_SHEET_ID` → Google Sheet ID
   * `TELEGRAM_BOT_TOKEN` → Telegram bot token
   * `TELEGRAM_CHAT_ID` → Telegram chat ID
   * `GITHUB_REPOSITORY` → owner/repo
   * `ISSUE_NUMBER` → GitHub issue number
   * `GITHUB_TOKEN` → workflow token or personal token

4. Commit and push the Python script (`update_sheet_v4.py`) and workflow (`update_live_data.yml`)

5. GitHub Actions will automatically update dashboards and CSVs

---

## Step 8: Monitoring & Maintenance

* Check GitHub Actions logs for errors
* Verify CSVs and dashboard updates in the repository
* Adjust alert thresholds in `update_sheet_v4.py` as needed
* Add new devices by logging them in the Google Sheet

---

## Step 9: Future Improvements

* Add more IoT metrics (e.g., CO₂, soil moisture)
* Enhance charts and visualizations
* Integrate Slack notifications or additional alert channels
* Deploy a web dashboard for live monitoring

---

***This repository provides a complete, automated IoT monitoring workflow from Google Sheets ingestion to GitHub visualization and alerting.***

```

---

This version now includes **embedded image placeholders** for the per-device charts, matching the workflow outputs.  

