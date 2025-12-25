import { Line } from "react-chartjs-2";
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

// Ensure registration (likely redundant if done in app, but safe)
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

export default function ZoomModal({ isOpen, onClose, title, data, labels }) {
    if (!isOpen) return null;

    // Determine unit
    let unit = "";
    const t = (title || "").toLowerCase();
    if (t.includes("temp")) unit = "°C";
    else if (t.includes("humid")) unit = "%";
    else if (t.includes("light")) unit = " Lux";

    const chartData = {
        labels: labels || [],
        datasets: [
            {
                label: title,
                data: data || [],
                borderColor: "rgb(59, 130, 246)",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                borderWidth: 2,
                pointRadius: 4, // Bigger points for visibility
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
            title: {
                display: true,
                text: `${title} History`,
                font: { size: 18 }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: (context) => `${context.parsed.y}${unit}`
                }
            }
        },
        scales: {
            x: {
                display: true,
                ticks: {
                    maxTicksLimit: 10,
                    // Show time part only on axis to keep it clean? 
                    // Or show full date if space permits.
                    // Let's show short date+time in zoom
                    callback: function (val, index) {
                        // val is index, this.getLabelForValue(val) is the string label
                        const label = this.getLabelForValue(val);
                        // Assume label is "DD/MM/YYYY HH:MM:SS"
                        // Return "DD/MM HH:MM"
                        try {
                            const parts = label.split(" ");
                            const dateParts = parts[0].split("/");
                            return `${dateParts[0]}/${dateParts[1]} ${parts[1].substring(0, 5)}`;
                        } catch (e) {
                            return label;
                        }
                    }
                }
            },
            y: {
                display: true,
                grid: { color: "#f1f5f9" }
            }
        }
    };

    const overlayStyle = {
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
        padding: "2rem"
    };

    const modalStyle = {
        backgroundColor: "white",
        borderRadius: "1rem",
        padding: "2rem",
        width: "100%",
        maxWidth: "1000px",
        height: "80vh",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
    };

    const closeBtnStyle = {
        position: "absolute",
        top: "1rem",
        right: "1rem",
        background: "#ef4444",
        color: "white",
        border: "none",
        borderRadius: "50%",
        width: "32px",
        height: "32px",
        cursor: "pointer",
        fontSize: "1.2rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
    };

    return (
        <div style={overlayStyle} onClick={onClose}>
            <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
                <button style={closeBtnStyle} onClick={onClose}>&times;</button>
                <div style={{ flex: 1, position: "relative" }}>
                    <Line data={chartData} options={options} />
                </div>
            </div>
        </div>
    );
}
