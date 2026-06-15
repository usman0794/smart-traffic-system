import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function VehicleChart({ data }) {
  const chartData = [
    { name: "Cars", value: data?.cars || 0 },
    { name: "Trucks", value: data?.trucks || 0 },
    { name: "Buses", value: data?.buses || 0 },
    { name: "Motorcycles", value: data?.motorcycles || 0 },
  ];

  const colors = ["#2563eb", "#16a34a", "#f97316", "#9333ea"];

  return (
    <div className="bg-white rounded-xl shadow p-5 h-80">
      <h2 className="text-lg font-semibold mb-4">Vehicle Type Distribution</h2>

      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" outerRadius={90}>
            {chartData.map((_, index) => (
              <Cell key={index} fill={colors[index]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
