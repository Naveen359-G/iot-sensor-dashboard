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

  return (
    <main className="p-6">
      <h1 className="text-3xl font-bold mb-4">🌡️ IoT Sensor Live Dashboard</h1>

      <InsightBox text="Latest insights from IoT devices" />

      {data.length > 0 &&
        columns
          .filter((col) => !isNaN(data[0]?.[col]))
          .map((col) => (
            <ChartCard key={col} title={col} data={data.map((d) => d[col])} />
          ))}
    </main>
  );
}
