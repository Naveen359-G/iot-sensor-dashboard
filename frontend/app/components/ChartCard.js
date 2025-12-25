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

export default function ChartCard({ title, data, labels, className }) {
  // Get latest value
  const latestValue = data.length > 0 ? data[data.length - 1] : "N/A";

  // Determine unit based on title
  let unit = "";
  const t = title.toLowerCase();
  if (t.includes("temp")) unit = "°C";
  else if (t.includes("humid")) unit = "%";
  else if (t.includes("light")) unit = " Lux";
  else if (t.includes("aqi")) unit = "";

  const chartData = {
    // If exact timestamps passed, use them. Else 1..N
    labels: labels || data.map((_, i) => i + 1),
    datasets: [
      {
        label: title,
        data: data,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false }, // Custom title used instead
      tooltip: {
        mode: 'index',
        intersect: false,
      }
    },
    scales: {
      x: {
        display: true, // Show X Axis
        tickets: {
          maxTicksLimit: 6,
          maxRotation: 0,
        },
        grid: { display: false }
      },
      y: {
        display: true, // Show Y Axis
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
    height: "350px", // Increased height for header
    display: "flex",
    flexDirection: "column"
  };

  const headerStyle = {
    marginBottom: "1rem",
  };

  const titleStyle = {
    fontSize: "0.875rem",
    fontWeight: 600,
    color: "var(--text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em"
  };

  const valueStyle = {
    fontSize: "2rem",
    fontWeight: 700,
    color: "var(--text-primary)",
    marginTop: "0.25rem"
  };

  return (
    <div style={cardStyle} className={className}>
      <div style={headerStyle}>
        <div style={titleStyle}>{title}</div>
        <div style={valueStyle}>
          {latestValue}<span style={{ fontSize: "1rem", color: "var(--text-secondary)", fontWeight: 500 }}>{unit}</span>
        </div>
      </div>
      <div style={{ flex: 1, position: "relative", minHeight: 0 }}>
        <Line options={options} data={chartData} />
      </div>
    </div>
  );
}
