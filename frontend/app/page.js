"use client";

import { useEffect, useState } from "react";
import ChartCard from "./components/ChartCard";
import InsightBox from "./components/InsightBox";

export default function Home() {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);

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
  }, []);

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

  return (
    <main className="container">
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.875rem", marginBottom: "0.5rem" }}>iot sensor dashboard</h1>
        <p style={{ color: "var(--text-secondary)" }}>Live environmental monitoring</p>
      </div>

      <InsightBox text="System active. Monitoring environmental parameters in real-time." />

      {data.length > 0 && (
        <div className="card-grid">
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
    </main>
  );
}
