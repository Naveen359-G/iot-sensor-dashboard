export default function UpdateStatus({ lastUpdated }) {
    if (!lastUpdated) return null;

    // Calculate Next Update (Last + 2 hours)
    const lastDate = new Date(lastUpdated);
    const nextDate = new Date(lastDate.getTime() + 120 * 60000);

    const formatTime = (d) => {
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (d) => {
        return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    };

    const isToday = new Date().toDateString() === lastDate.toDateString();

    const containerStyle = {
        display: "flex",
        gap: "1.5rem",
        fontSize: "0.875rem",
        color: "var(--text-secondary)",
        background: "white",
        padding: "0.5rem 1rem",
        borderRadius: "2rem",
        border: "1px solid var(--border-color)",
        boxShadow: "var(--shadow-sm)",
        marginTop: "0.5rem"
    };

    const itemStyle = {
        display: "flex",
        alignItems: "center",
        gap: "0.5rem"
    };

    return (
        <div style={containerStyle}>
            <div style={itemStyle}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981" }}></span>
                <span>Last Sensor Data: <strong>{isToday ? formatTime(lastDate) : `${formatDate(lastDate)} ${formatTime(lastDate)}`}</strong></span>
            </div>
            <div style={itemStyle}>
                <span>Next Fetch: <strong>{formatTime(nextDate)}</strong></span>
            </div>
        </div>
    );
}
