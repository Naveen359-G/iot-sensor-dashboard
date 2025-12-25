export default function DeviceSelector({ devices, selectedDevice, onSelect }) {
    // Always render to avoid UI "popping" or confusing the user
    const hasDevices = devices && devices.length > 0;

    const containerStyle = {
        marginBottom: "1.5rem",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
    };

    const labelStyle = {
        fontWeight: 500,
        color: "#374151",
    };

    const selectStyle = {
        display: "block",
        padding: "0.5rem 0.75rem",
        backgroundColor: "#fff",
        border: "1px solid #d1d5db",
        borderRadius: "0.375rem",
        boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        fontSize: "0.875rem",
        lineHeight: "1.25rem",
        outline: "none",
        minWidth: "200px",
        cursor: hasDevices ? "pointer" : "not-allowed",
        opacity: hasDevices ? 1 : 0.7
    };

    return (
        <div style={containerStyle}>
            <label htmlFor="device-select" style={labelStyle}>
                Select Device:
            </label>
            <select
                id="device-select"
                value={selectedDevice}
                onChange={(e) => onSelect(e.target.value)}
                style={selectStyle}
                disabled={!hasDevices}
            >
                {hasDevices ? (
                    devices.map((device) => (
                        <option key={device} value={device}>
                            {device}
                        </option>
                    ))
                ) : (
                    <option>Waiting for data...</option>
                )}
            </select>
        </div>
    );
}
