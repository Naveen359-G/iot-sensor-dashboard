"use client";

import { useState, useEffect } from "react";

export default function ControlPanel({ status, onIntervalChange, onCalibrate }) {
    const [interval, setInterval] = useState(20);
    const [saving, setSaving] = useState(false);
    const [calibrating, setCalibrating] = useState(false);

    useEffect(() => {
        if (status && status.interval) {
            setInterval(status.interval);
        }
    }, [status]);

    const handleSave = async () => {
        setSaving(true);
        await onIntervalChange(interval);
        setSaving(false);
    };

    const handleCalibrate = async () => {
        setCalibrating(true);
        await onCalibrate();
        setCalibrating(false);
    };

    return (
        <div style={{ marginTop: "2rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "1rem" }}>
                <label htmlFor="interval-input" style={{ whiteSpace: "nowrap" }}>Interval (minutes):</label>
                <input
                    id="interval-input"
                    type="number"
                    value={interval}
                    onChange={(e) => setInterval(parseInt(e.target.value) || 0)}
                    style={{
                        padding: "5px 10px",
                        borderRadius: "4px",
                        border: "none",
                        width: "80px",
                        color: "#000"
                    }}
                />
                <button
                    onClick={handleSave}
                    disabled={saving}
                    style={{
                        padding: "5px 15px",
                        borderRadius: "4px",
                        border: "none",
                        backgroundColor: "#fff",
                        color: "#000",
                        cursor: saving ? "wait" : "pointer"
                    }}
                >
                    {saving ? "Saving..." : "Save"}
                </button>
            </div>

            <button
                onClick={handleCalibrate}
                disabled={calibrating}
                style={{
                    padding: "8px 15px",
                    borderRadius: "4px",
                    border: "none",
                    backgroundColor: "#fff",
                    color: "#000",
                    cursor: calibrating ? "wait" : "pointer",
                    marginBottom: "1.5rem"
                }}
            >
                {calibrating ? "Calibrating..." : "Calibrate MQ135"}
            </button>

            <div style={{ fontSize: "0.9rem", color: "#ccc" }}>
                <p style={{ marginBottom: "0.5rem" }}>
                    Last captured at: <span style={{ fontWeight: "bold", color: "#fff" }}>{status?.last_captured || "N/A"}</span>
                </p>
                <p>
                    Next capture expected at: <span style={{ fontWeight: "bold", color: "#fff" }}>{status?.next_capture || "N/A"}</span>
                </p>
            </div>
        </div>
    );
}
