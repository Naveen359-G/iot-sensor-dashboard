"use client";

import { useEffect, useState } from "react";
import ChartCard from "./components/ChartCard";
import InsightBox from "./components/InsightBox";
import DeviceSelector from "./components/DeviceSelector";
import DateRangeSelector from "./components/DateRangeSelector";

export default function Home() {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState("");
  const [days, setDays] = useState(null); // null = All Time

  // 1. Fetch Devices on Mount
  useEffect(() => {
    async function fetchDevices() {
      try {
        const res = await fetch("/api/devices");
        if (res.ok) {
          const json = await res.json();
          const deviceList = json.devices || [];
          setDevices(deviceList);
          if (deviceList.length > 0) {
            setSelectedDevice(deviceList[0]);
          }
        }
      } catch (error) {
        console.error("Error fetching devices:", error);
      }
    }
    fetchDevices();
  }, []);

  // 2. Fetch Data when Device or Days Changes
  useEffect(() => {
    async function fetchData() {
      try {
        // Construct URL
        const params = new URLSearchParams();
        if (selectedDevice) params.append("device_id", selectedDevice);
        if (days) params.append("days", days);

        const url = `/api/data/json?${params.toString()}`;

        const dataRes = await fetch(url);
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

    // Only fetch if we have devices loaded (or just fetch all if none coexist)
    fetchData();
  }, [selectedDevice, days]);

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
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold">🌡️ IoT Sensor Live Dashboard</h1>
          <p className="text-gray-500 mt-1">Real-time environmental monitoring</p>
        </div>
        <div className="flex flex-col items-end gap-2 mt-4 md:mt-0">
          <DeviceSelector
            devices={devices}
            selectedDevice={selectedDevice}
            onSelect={setSelectedDevice}
          />
          <DateRangeSelector
            selectedRange={days}
            onSelect={setDays}
          />
        </div>
      </div>

      <InsightBox text={`Viewing real-time data for ${selectedDevice || "all devices"}.`} />

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

      {data.length === 0 && (
        <p className="text-gray-500">No data available for this device.</p>
      )}
    </main>
  );
}

