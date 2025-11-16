import { Line } from "react-chartjs-2";

export default function ChartCard({ title, data }) {
  return (
    <div className="mb-6 p-4 bg-white shadow rounded-xl">
      <h2 className="font-semibold mb-2">{title}</h2>
      <Line
        data={{
          labels: data.map((_, i) => i),
          datasets: [{ data }]
        }}
      />
    </div>
  );
}
