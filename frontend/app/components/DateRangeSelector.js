export default function DateRangeSelector({ selectedRange, onSelect }) {
    const ranges = [
        { label: "Last 24h", value: 1 },
        { label: "Last 7 Days", value: 7 },
        { label: "Last 30 Days", value: 30 },
        { label: "Last 90 Days", value: 90 },
        { label: "All Time", value: null },
    ];

    const containerStyle = {
        display: "flex",
        gap: "0.5rem",
        marginBottom: "1.5rem",
        flexWrap: "wrap"
    };

    const getButtonStyle = (isActive) => ({
        padding: "0.5rem 1rem",
        borderRadius: "0.5rem",
        fontSize: "0.875rem",
        fontWeight: 500,
        cursor: "pointer",
        border: "none",
        transition: "all 0.2s",
        backgroundColor: isActive ? "var(--accent-color)" : "#fff",
        color: isActive ? "#fff" : "var(--text-secondary)",
        boxShadow: isActive ? "0 2px 4px rgba(59, 130, 246, 0.3)" : "0 1px 2px rgba(0,0,0,0.05)",
    });

    return (
        <div style={containerStyle}>
            {ranges.map((range) => (
                <button
                    key={range.label}
                    onClick={() => onSelect(range.value)}
                    style={getButtonStyle(selectedRange === range.value)}
                >
                    {range.label}
                </button>
            ))}
        </div>
    );
}
