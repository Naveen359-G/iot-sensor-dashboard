"use client";

import { useEffect, useState } from "react";
import ChartCard from "./components/ChartCard";
import InsightBox from "./components/InsightBox";
import ControlPanel from "./components/ControlPanel";
import ParameterList from "./components/ParameterList";

export default function Home() {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [status, setStatus] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const json = await res.json();
        setStatus(json);
      }
    } catch (e) {
      console.error("Error fetching status:", e);
    }
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const dataRes = await fetch("/api/data/json");
        if (!dataRes.ok) throw new Error("Failed to fetch data");
        const dataJson = await dataRes.json();
        setData(dataJson);

        const colRes = await fetch("/api/data/columns");
        if (colRes.ok) {
          const colJson = await colRes.json();
          setColumns(colJson.columns || []);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
    fetchData();
    fetchStatus();
  }, []);

  const handleIntervalChange = async (newInterval) => {
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: newInterval })
      });
      if (res.ok) {
        fetchStatus(); // Refresh status
      }
    } catch (e) {
      console.error("Error updating interval:", e);
    }
  };

  const handleCalibrate = async () => {
    try {
      const res = await fetch("/api/calibrate", { method: "POST" });
      if (res.ok) {
        fetchStatus();
      }
    } catch (e) {
      console.error("Error calibration:", e);
    }
  };

  // Helper to get data series for a specific metric
  const getDataFor = (keyword) => {
    const colName = columns.find(c => c.toLowerCase().includes(keyword.toLowerCase()));
    if (!colName || data.length === 0) return null;
    return {
      title: colName,
      series: data.map(d => d[colName])
    };
  };

  // Specific metrics
  const temp = getDataFor("temperature");
  const humidity = getDataFor("humidity");
  const light = getDataFor("light");
  const aqi = getDataFor("aqi");
  const heap = getDataFor("heap") || getDataFor("health") || getDataFor("device"); // Fallbacks

  const latestData = data.length > 0 ? data[data.length - 1] : null;

  return (
    <main className="container">
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.875rem", marginBottom: "0.5rem" }}>iot sensor dashboard</h1>
        <p style={{ color: "var(--text-secondary)" }}>Live environmental monitoring</p>
      </div>

      <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div style={{ flex: "1", minWidth: "350px" }}>
          {/* New Parameter List Block */}
          {latestData && (
            <ParameterList data={latestData} />
          )}

          {/* Controls */}
          <ControlPanel
            status={status}
            onIntervalChange={handleIntervalChange}
            onCalibrate={handleCalibrate}
          />
        </div>

        <div style={{ flex: "1", minWidth: "350px" }}>
          {/* Existing Charts */}
          <InsightBox text="System active. Monitoring environmental parameters in real-time." />

          {data.length > 0 && (
            <div className="card-grid" style={{ gridTemplateColumns: "1fr" }}> {/* Force single column for right side */}
              {/* Row 1 */}
              {temp && <ChartCard title={temp.title} data={temp.series} />}
              {humidity && <ChartCard title={humidity.title} data={humidity.series} />}

              {/* Row 2 */}
              {light && <ChartCard title={light.title} data={light.series} />}
              {aqi && <ChartCard title={aqi.title} data={aqi.series} />}

              {/* Row 3 - Full Width for Heap/Health */}
              {heap && <ChartCard className="full-width" title={heap.title} data={heap.series} />}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
