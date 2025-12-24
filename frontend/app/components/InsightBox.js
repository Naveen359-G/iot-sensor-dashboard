export default function InsightBox({ text }) {
  return (
    <div className="p-4 mb-4 bg-blue-100 rounded-xl shadow-md">
      <h2 className="font-semibold">AI Summary</h2>
      <p className="text-gray-700">{text}</p>
    </div>
  );
}
