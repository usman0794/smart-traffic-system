import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function DensityChart({ snapshots }) {
  // Backend sends latest first, chart needs oldest first
  const data = [...snapshots].reverse().map((item, index) => ({
    frame: index + 1,
    total: item.total_count,
    active: item.active_vehicles,
  }));

  return (
    <div className="bg-white rounded-xl shadow p-5 h-80">
      <h2 className="text-lg font-semibold mb-4">Traffic Count Trend</h2>

      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="frame" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="total" stroke="#2563eb" />
          <Line type="monotone" dataKey="active" stroke="#16a34a" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
