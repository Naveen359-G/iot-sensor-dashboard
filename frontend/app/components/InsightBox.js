export default function InsightBox({ text }) {
  const boxStyle = {
    background: "#eff6ff", // Light blue tint
    borderRadius: "var(--radius-lg)",
    padding: "1.5rem",
    marginBottom: "2rem",
    border: "1px solid #dbeafe",
    color: "#1e3a8a",
  };

  return (
    <div style={boxStyle}>
      <h2 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>AI Summary</h2>
      <p style={{ lineHeight: 1.6 }}>{text}</p>
    </div>
  );
}
