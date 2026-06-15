import { useState } from "react";
import api from "../services/api";

export default function UploadVideo() {
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("");
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    setFile(selectedFile || null);
    setFilename("");

    // Reset dashboard when new video selected
    localStorage.setItem("resetDashboard", "true");

    if (selectedFile) {
      setMessage(`Selected: ${selectedFile.name}`);
    } else {
      setMessage("");
    }
  };

  const uploadVideo = async () => {
    if (!file) {
      alert("Please select a video first");
      return;
    }

    try {
      setUploading(true);

      // Reset dashboard when new upload starts
      localStorage.setItem("resetDashboard", "true");
      setMessage("Uploading video...");

      const formData = new FormData();
      formData.append("file", file);

      const res = await api.post("/videos/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setFilename(res.data.filename);
      setMessage(`Uploaded successfully: ${res.data.filename}`);
    } catch (error) {
      console.error("Upload error:", error);
      setMessage("Upload failed. Check backend console.");
    } finally {
      setUploading(false);
    }
  };

  const processVideo = async () => {
    if (!filename) {
      alert("Please upload the video first");
      return;
    }

    try {
      setProcessing(true);
      setMessage("Processing video... This may take some time.");

      const res = await api.post(`/videos/process/${filename}`);

      setMessage(`Processed successfully: ${res.data.output_video}`);
    } catch (error) {
      console.error("Processing error:", error);
      setMessage("Processing failed. Check backend console.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="p-6 bg-slate-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-6">Upload Traffic Video</h1>

      <div className="bg-white rounded-xl shadow p-6 max-w-xl">
        <label className="block mb-2 font-medium">Select traffic video</label>

        <input
          type="file"
          accept=".mp4,.avi,.mov,.mkv,video/*"
          onChange={handleFileChange}
          className="block w-full mb-4 border border-slate-300 rounded-lg p-2"
        />

        <div className="flex gap-4">
          <button
            onClick={uploadVideo}
            disabled={!file || uploading || processing}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>

          <button
            onClick={processVideo}
            disabled={!filename || uploading || processing}
            className="bg-green-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {processing ? "Processing..." : "Process Video"}
          </button>
        </div>

        {message && <p className="mt-4 text-slate-700">{message}</p>}

        {filename && (
          <p className="mt-2 text-green-700">Ready to process: {filename}</p>
        )}
      </div>
    </div>
  );
}
