import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function ChartCard({ title, data, className }) {
  const chartData = {
    labels: data.map((_, i) => i + 1),
    datasets: [
      {
        label: title,
        data: data,
        borderColor: "rgb(59, 130, 246)", // accent-color #3b82f6
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.4, // Smooth curves
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: title,
        color: "#64748b",
        font: {
          size: 14,
          weight: 500
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      }
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        border: { display: false },
        grid: {
          color: "#f1f5f9",
        },
        ticks: {
          color: "#94a3b8",
          font: { size: 10 }
        }
      }
    }
  };

  const cardStyle = {
    background: "var(--card-bg)",
    borderRadius: "var(--radius-lg)",
    boxShadow: "var(--shadow-md)",
    padding: "1.5rem",
    border: "1px solid var(--border-color)",
    height: "300px", // Fixed height for consistent grid
    display: "flex",
    flexDirection: "column"
  };

  return (
    <div style={cardStyle} className={className}>
      <div style={{ flex: 1, position: "relative" }}>
        <Line options={options} data={chartData} />
      </div>
    </div>
  );
}
