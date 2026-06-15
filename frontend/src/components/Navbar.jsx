import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center">
      <h1 className="text-xl font-bold">Smart Traffic System</h1>

      <div className="flex gap-6">
        <Link to="/">Dashboard</Link>
        <Link to="/upload">Upload Video</Link>
        <Link to="/analytics">Analytics</Link>
      </div>
    </nav>
  );
}
