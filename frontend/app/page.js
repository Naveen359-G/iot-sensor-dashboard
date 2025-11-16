"use client";

import { useEffect, useState } from "react";
import ChartCard from "./components/ChartCard";
import InsightBox from "./components/InsightBox";

export default function Home() {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    fetch("/api/data/json")
      .then(res => res.json())
      .then(setData);

    fetch("/api/data/columns")
      .then(res => res.json())
      .then(r => setColumns(r.columns || []));
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
