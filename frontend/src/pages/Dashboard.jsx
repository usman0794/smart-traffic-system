import { useEffect, useState, useCallback } from "react";
import api from "../services/api";
import StatsCard from "../components/StatsCard";
import VehicleChart from "../components/VehicleChart";
import DensityChart from "../components/DensityChart";
import RecentEvents from "../components/RecentEvents";

// Skeleton Loader Components
const SkeletonStatsCard = () => (
  <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
    <div className="h-8 bg-gray-200 rounded w-16"></div>
  </div>
);

const SkeletonChart = () => (
  <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
    <div className="h-6 bg-gray-200 rounded w-40 mb-6"></div>
    <div className="space-y-3">
      <div className="h-64 bg-gray-200 rounded-lg"></div>
      <div className="flex justify-between">
        <div className="h-4 bg-gray-200 rounded w-20"></div>
        <div className="h-4 bg-gray-200 rounded w-20"></div>
        <div className="h-4 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  </div>
);

const SkeletonRecentEvents = () => (
  <div className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
    <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
    <div className="space-y-3">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const SkeletonDashboard = () => (
  <div className="p-6 bg-slate-50 min-h-screen">
    <div className="mb-8">
      <div className="h-9 bg-gray-200 rounded-lg w-64 animate-pulse"></div>
    </div>
    {/* Row 1 Skeleton */}
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
      {[...Array(5)].map((_, i) => (
        <SkeletonStatsCard key={i} />
      ))}
    </div>
    {/* Row 2 Skeleton */}
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      {[...Array(4)].map((_, i) => (
        <SkeletonStatsCard key={i} />
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <SkeletonChart />
      <SkeletonChart />
    </div>
    <div className="mt-6">
      <SkeletonRecentEvents />
    </div>
  </div>
);

const emptySummary = {
  total_vehicles: 0,
  total_vehicles_trend: 0,
  incoming: 0,
  outgoing: 0,
  cars: 0,
  trucks: 0,
  buses: 0,
  motorcycles: 0,
  current_density: "Low",
  accidents: 0,
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  useEffect(() => {
    const shouldReset = localStorage.getItem("resetDashboard");

    if (shouldReset === "true") {
      setSummary(emptySummary);
      setSnapshots([]);
      setRecentEvents([]);
      localStorage.removeItem("resetDashboard");
    }
  }, []);

  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      const [summaryRes, snapshotsRes, eventsRes] = await Promise.allSettled([
        api.get("/analytics/summary"),
        api.get("/analytics/snapshots"),
        api.get("/analytics/recent-events"),
      ]);

      if (summaryRes.status === "fulfilled") {
        setSummary(summaryRes.value.data);
      }
      if (snapshotsRes.status === "fulfilled") {
        setSnapshots(snapshotsRes.value.data);
      }
      if (eventsRes.status === "fulfilled") {
        setRecentEvents(eventsRes.value.data);
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();

    const interval = setInterval(fetchDashboardData, refreshInterval);

    return () => clearInterval(interval);
  }, [fetchDashboardData, refreshInterval]);

  const formatLastUpdated = () => {
    if (!lastUpdated) return "";
    return lastUpdated.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // Density value formatter
  const formatDensity = (density) => {
    if (typeof density === "number") {
      if (density > 70) return "High";
      if (density > 40) return "Medium";
      return "Low";
    }
    return density || "Medium";
  };

  if (loading && !summary) {
    return <SkeletonDashboard />;
  }

  if (error && !summary) {
    return (
      <div className="p-6 bg-slate-50 min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-red-600 text-lg mb-2 font-semibold">{error}</div>
          <p className="text-gray-500 mb-4">
            Please check your connection and try again
          </p>
          <button
            onClick={fetchDashboardData}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm"
          >
            Retry Now
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
            Traffic Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time traffic monitoring & analytics
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Refresh Control */}
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-600"
          >
            <option value={2000}>2s</option>
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
          </select>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-full shadow-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-600 font-medium">Live</span>
          </div>
          <div className="text-xs text-gray-400 bg-white px-3 py-1.5 rounded-full shadow-sm">
            Updated: {formatLastUpdated()}
          </div>
        </div>
      </div>

      {/* Stats Grid - Clean 2 Row Layout */}
      <div className="space-y-4 mb-6">
        {/* Row 1: Key Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatsCard
            title="Total Vehicles"
            value={summary.total_vehicles}
            icon="🚗"
            trend={summary.total_vehicles_trend}
            color="slate"
          />
          <StatsCard
            title="Incoming"
            value={summary.incoming}
            icon="⬅️"
            color="blue"
          />
          <StatsCard
            title="Outgoing"
            value={summary.outgoing}
            icon="➡️"
            color="green"
          />
          <StatsCard
            title="Density"
            value={formatDensity(summary.current_density)}
            icon="🚦"
            color="emerald"
            subtitle={
              typeof summary.current_density === "number"
                ? `${summary.current_density}%`
                : undefined
            }
          />
          <StatsCard
            title="Accidents"
            value={summary.accidents}
            icon="⚠️"
            color="red"
            alert={summary.accidents > 0}
          />
        </div>

        {/* Row 2: Vehicle Breakdown */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatsCard
            title="Cars"
            value={summary.cars}
            icon="🚙"
            color="purple"
          />
          <StatsCard
            title="Trucks"
            value={summary.trucks}
            icon="🚛"
            color="orange"
          />
          <StatsCard
            title="Buses"
            value={summary.buses}
            icon="🚌"
            color="amber"
          />
          <StatsCard
            title="Motorcycles"
            value={summary.motorcycles}
            icon="🏍️"
            color="indigo"
          />
        </div>
      </div>

      {/* Charts and Events Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all duration-300">
          <VehicleChart data={summary} />
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all duration-300">
          <DensityChart snapshots={snapshots} />
        </div>
      </div>

      {/* Recent Events */}
      <div className="mt-6">
        <RecentEvents events={recentEvents} />
      </div>

      {/* Refresh Indicator */}
      {loading && summary && (
        <div className="fixed bottom-4 right-4 bg-white rounded-full shadow-lg px-4 py-2 text-sm text-gray-600 animate-pulse">
          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
          Refreshing data...
        </div>
      )}
    </div>
  );
}
