"use client";

function ParameterRow({ label, value, unit, status, icon }) {
    const isAlert = status === "Alert" || status === "Hazardous" || status?.includes("Alert");
    const isGood = status === "Good" || status === "GOOD" || status === "Normal" || status === "No smoke detected";

    // Custom logic for status color dot if needed, or just text color
    let statusColor = "#fff";
    if (isGood) statusColor = "#4ade80"; // green
    if (isAlert) statusColor = "#f87171"; // red

    return (
        <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "10px 0",
            borderBottom: "1px solid #333"
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>{icon}</span>
                <span style={{ fontWeight: "500" }}>{label}</span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {value !== undefined && (
                    <span style={{ fontWeight: "bold" }}>
                        {value} <span style={{ fontSize: "0.9em", color: "#aaa" }}>{unit}</span>
                    </span>
                )}

                {status && (
                    <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                        <span>{status}</span>
                        {/* Simple dot indicator */}
                        <div style={{
                            width: "12px",
                            height: "12px",
                            borderRadius: "50%",
                            backgroundColor: statusColor
                        }}></div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ParameterList({ data }) {
    if (!data) return null;

    // Extract values safely
    const health = data.Device_Health || "GOOD"; // Defaulting as example
    const temp = data["Temperature_°C"] || data.Temperature;
    const hum = data["Humidity_%"] || data.Humidity;
    const light = data.Light;
    const aqiVal = data.AQI_Value;
    const aqiStatus = data.AQI_Status || "Unknown";
    const eco2 = data["eCO₂ (ppm)"] || data.eCO2 || 0;
    const smoke = data.Smoke_Status || "No smoke detected";

    return (
        <div style={{ backgroundColor: "rgba(0,0,0,0.3)", padding: "20px", borderRadius: "10px", marginBottom: "2rem" }}>
            <h2 style={{ color: "#4ade80", textAlign: "center", marginBottom: "20px" }}>Indoor Farm Data</h2>

            <div style={{ marginBottom: "15px", fontSize: "0.9em", color: "#aaa" }}>
                <p>Device: indoor-farm-01</p>
                <p>Date: {new Date().toLocaleDateString("en-GB")} Time: {new Date().toLocaleTimeString()}</p>
            </div>

            <ParameterRow icon="❤️" label="Device Health" status={health} />
            <ParameterRow icon="🌡️" label="Temperature" value={temp} unit="°C" />
            <ParameterRow icon="💧" label="Humidity" value={hum} unit="%" />
            <ParameterRow icon="💡" label="Light (Lux)" value={light} />
            <ParameterRow icon="📊" label="AQI Value" value={aqiVal} />
            <ParameterRow icon="⚠️" label="AQI Status" status={aqiStatus} />
            <ParameterRow icon="🟢" label="eCO₂ (ppm)" value={eco2} />
            <ParameterRow icon="🔥" label="Smoke Status" status={smoke} />
        </div>
    );
}
