import { useEffect, useState } from "react";
import api from "../services/api";

export default function Analytics() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    api.get("/analytics/vehicle-events").then((res) => {
      setEvents(res.data);
    });
  }, []);

  return (
    <div className="p-6 bg-slate-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Vehicle Events</h1>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-900 text-white">
            <tr>
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">Vehicle</th>
              <th className="p-3 text-left">Direction</th>
              <th className="p-3 text-left">Track ID</th>
              <th className="p-3 text-left">Time</th>
            </tr>
          </thead>

          <tbody>
            {events.map((event) => (
              <tr key={event.id} className="border-b">
                <td className="p-3">{event.id}</td>
                <td className="p-3">{event.vehicle_type}</td>
                <td className="p-3">{event.direction}</td>
                <td className="p-3">{event.track_id}</td>
                <td className="p-3">
                  {new Date(event.crossing_time).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
