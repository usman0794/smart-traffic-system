import { useEffect, useState } from "react";
import api from "../services/api";

export default function RecentEvents() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    api
      .get("/analytics/vehicle-events")
      .then((res) => setEvents(res.data))
      .catch(console.error);
  }, []);

  const formatPakistanTime = (time) => {
    if (!time) return "-";

    return new Date(time + "Z").toLocaleString("en-PK", {
      timeZone: "Asia/Karachi",
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 overflow-hidden">
      <h2 className="text-xl font-semibold mb-4 text-slate-800">
        Recent Vehicle Events
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-slate-100 text-slate-600">
              <th className="px-4 py-3 text-left font-semibold">ID</th>
              <th className="px-4 py-3 text-left font-semibold">Vehicle</th>
              <th className="px-4 py-3 text-left font-semibold">Direction</th>
              <th className="px-4 py-3 text-left font-semibold">Track ID</th>
              <th className="px-4 py-3 text-left font-semibold">Time</th>
            </tr>
          </thead>

          <tbody>
            {events.slice(0, 10).map((event) => (
              <tr
                key={event.id}
                className="border-b border-slate-100 hover:bg-slate-50 transition"
              >
                <td className="px-4 py-3 text-slate-700">{event.id}</td>
                <td className="px-4 py-3 capitalize text-slate-700">
                  {event.vehicle_type}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      event.direction === "incoming"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {event.direction}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700">{event.track_id}</td>
                <td className="px-4 py-3 text-slate-600">
                  {formatPakistanTime(event.crossing_time)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
