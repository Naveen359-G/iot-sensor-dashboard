export default function UpdateStatus({ lastUpdated }) {
    if (!lastUpdated) return null;

    // Calculate Next Update (Last + 45 mins)
    const lastDate = new Date(lastUpdated);
    const nextDate = new Date(lastDate.getTime() + 45 * 60000);

    const formatTime = (d) => {
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

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
                <span>Last Updated: <strong>{formatTime(lastDate)}</strong></span>
            </div>
            <div style={itemStyle}>
                <span>Next Update: <strong>{formatTime(nextDate)}</strong></span>
            </div>
        </div>
    );
}
