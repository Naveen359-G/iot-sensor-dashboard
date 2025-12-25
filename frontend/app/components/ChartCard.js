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

export default function ChartCard({ title, data, labels, className, onClick }) {
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
    // Labels are now full datetime strings "DD/MM/YYYY HH:MM:SS"
    labels: labels || data.map((_, i) => i + 1),
    datasets: [
      {
        label: title,
        data: data,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        borderWidth: 2,
        pointRadius: 2, // Small points in mini view
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
        callbacks: {
          // Show value with unit
          label: (context) => `${context.parsed.y}${unit}`
        }
      }
    },
    scales: {
      x: {
        display: true, // Show X Axis
        ticks: {
          maxTicksLimit: 6,
          maxRotation: 0,
          callback: function (val, index) {
            // val is index, getLabelForValue gives the string
            const label = this.getLabelForValue(val);
            // Extract just the time "HH:MM" from "DD/MM/YYYY HH:MM:SS"
            try {
              // Split by space -> ["DD/MM/YYYY", "HH:MM:SS"]
              // Take "HH:MM"
              const timePart = label.split(" ")[1];
              if (timePart) return timePart.substring(0, 5);
              return label;
            } catch (e) {
              return label;
            }
          }
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
    },
    // optimizations
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  const cardStyle = {
    background: "var(--card-bg)",
    borderRadius: "var(--radius-lg)",
    boxShadow: "var(--shadow-md)",
    padding: "1.5rem",
    border: "1px solid var(--border-color)",
    height: "350px",
    display: "flex",
    flexDirection: "column",
    cursor: onClick ? "pointer" : "default", // Show pointer
    transition: "transform 0.2s", // Subtle hover effect
  };

  // Add hover effect via simplified inline style? React specific
  // We'll rely on the cursor for now.

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
    <div style={cardStyle} className={className} onClick={onClick}>
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
