import { useState, useRef } from "react";
import api from "../services/api";
import {
  FaUpload,
  FaPlay,
  FaStop,
  FaSpinner,
  FaCheckCircle,
  FaExclamationTriangle,
  FaVideo,
  FaFileVideo,
  FaTrash,
  FaRoad,
} from "react-icons/fa";
import { MdCloudUpload, MdVideoSettings } from "react-icons/md";

export default function UploadVideo() {
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [roadMode, setRoadMode] = useState("two_way");
  const [dragActive, setDragActive] = useState(false);
  const [streamUrl, setStreamUrl] = useState("");
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    handleFileSelect(e.target.files[0]);
  };

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;

    if (selectedFile.size > 500 * 1024 * 1024) {
      setMessage("File too large. Maximum size is 500MB.");
      setMessageType("error");
      return;
    }

    if (!selectedFile.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
      setMessage("Please select a valid video file (MP4, AVI, MOV, MKV).");
      setMessageType("error");
      return;
    }

    // Stop any running live stream before loading a new file
    setStreamUrl("");
    setFile(selectedFile);
    setFilename("");
    localStorage.setItem("resetDashboard", "true");
    setMessage(
      `Selected: ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)`,
    );
    setMessageType("info");
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFileSelect(e.dataTransfer.files[0]);
  };

  const clearFile = () => {
    setFile(null);
    setFilename("");
    setMessage("");
    setMessageType("info");
    setStreamUrl("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadVideo = async () => {
    if (!file) {
      setMessage("Please select a video first.");
      setMessageType("error");
      return;
    }

    try {
      setUploading(true);
      localStorage.setItem("resetDashboard", "true");
      setMessage("Uploading video...");
      setMessageType("info");

      const formData = new FormData();
      formData.append("file", file);

      const res = await api.post("/videos/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          setMessage(`Uploading... ${percentCompleted}%`);
        },
      });

      setFilename(res.data.filename);
      setMessage(`Uploaded successfully: ${res.data.filename}`);
      setMessageType("success");
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Upload error:", error);
      setMessage("Upload failed. Please check your connection and try again.");
      setMessageType("error");
    } finally {
      setUploading(false);
    }
  };

  const processVideo = async () => {
    if (!filename) {
      setMessage("Please upload the video first.");
      setMessageType("error");
      return;
    }

    try {
      setProcessing(true);
      setMessage("Processing video... This may take several minutes.");
      setMessageType("info");

      const res = await api.post(`/videos/process/${filename}`, null, {
        params: {
          road_mode: roadMode,
        },
        timeout: 300000,
      });

      setMessage(`Processed successfully: ${res.data.output_video}`);
      setMessageType("success");

      setTimeout(() => {
        setFilename("");
      }, 3000);
    } catch (error) {
      console.error("Processing error:", error);
      setMessage("Processing failed. Please check the backend console.");
      setMessageType("error");
    } finally {
      setProcessing(false);
    }
  };

  const watchLive = () => {
    if (!filename) {
      setMessage("Please upload the video first.");
      setMessageType("error");
      return;
    }

    const base = api.defaults.baseURL || "";
    setStreamUrl(
      `${base}/videos/stream/${filename}?road_mode=${roadMode}&t=${Date.now()}`,
    );
    setMessage("Live detection started — watch the feed below.");
    setMessageType("info");
  };

  // STOP: removes the <img>, which closes the MJPEG connection. The backend
  // generator then receives GeneratorExit and stops processing immediately.
  const stopLive = () => {
    setStreamUrl("");
    setMessage("Live stream stopped. You can upload a new video.");
    setMessageType("info");
  };

  // STOP & RESET: stop the stream AND clear everything for a fresh upload.
  const stopAndReset = () => {
    setStreamUrl("");
    setFile(null);
    setFilename("");
    setMessage("Stopped. Ready for a new video.");
    setMessageType("info");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const MessageIcon = () => {
    if (messageType === "success") {
      return <FaCheckCircle className="text-green-500" />;
    }

    if (messageType === "error") {
      return <FaExclamationTriangle className="text-red-500" />;
    }

    return <FaVideo className="text-blue-500" />;
  };

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 min-h-screen">
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
            Upload Traffic Video
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload and process traffic videos for intelligent analysis
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-full shadow-sm">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-600 font-medium">Ready</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300 p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <MdCloudUpload className="text-blue-500" />
              Upload Video
            </h2>

            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                dragActive
                  ? "border-blue-500 bg-blue-50"
                  : file
                    ? "border-green-500 bg-green-50"
                    : "border-gray-300 hover:border-blue-400"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {file ? (
                <div className="space-y-3">
                  <FaFileVideo className="text-4xl text-green-500 mx-auto" />
                  <p className="font-semibold text-slate-700">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>

                  <button
                    onClick={clearFile}
                    className="text-red-500 hover:text-red-700 text-sm flex items-center gap-1 mx-auto"
                  >
                    <FaTrash /> Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <FaUpload className="text-4xl text-gray-400 mx-auto" />
                  <div>
                    <p className="font-semibold text-slate-700">
                      Drag & drop your video here
                    </p>
                    <p className="text-sm text-gray-500">
                      or click to browse files
                    </p>
                  </div>
                  <p className="text-xs text-gray-400">
                    Supports: MP4, AVI, MOV, MKV (Max 500MB)
                  </p>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.avi,.mov,.mkv,video/*"
                onChange={handleFileChange}
                className="hidden"
              />

              {!file && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                >
                  Browse Files
                </button>
              )}
            </div>

            <div className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  <FaRoad className="inline mr-2 text-blue-500" />
                  Road Mode
                </label>

                <select
                  value={roadMode}
                  onChange={(e) => setRoadMode(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 text-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                  disabled={processing}
                >
                  <option value="one_way">One Way Traffic</option>
                  <option value="two_way">Two Way Traffic</option>
                </select>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={uploadVideo}
                  disabled={!file || uploading || processing}
                  className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {uploading ? (
                    <>
                      <FaSpinner className="animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <MdCloudUpload />
                      Upload Video
                    </>
                  )}
                </button>

                <button
                  onClick={processVideo}
                  disabled={!filename || uploading || processing}
                  className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {processing ? (
                    <>
                      <FaSpinner className="animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FaPlay />
                      Process Video
                    </>
                  )}
                </button>

                {streamUrl ? (
                  <button
                    onClick={stopLive}
                    className="flex items-center gap-2 px-6 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-black transition font-medium"
                  >
                    <FaStop />
                    Stop Live
                  </button>
                ) : (
                  <button
                    onClick={watchLive}
                    disabled={!filename || uploading}
                    className="flex items-center gap-2 px-6 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    <FaVideo />
                    Watch Live
                  </button>
                )}

                {(filename || streamUrl) && (
                  <button
                    onClick={stopAndReset}
                    className="px-4 py-2.5 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition font-medium"
                  >
                    <FaTrash className="inline mr-1" />
                    Stop & New Video
                  </button>
                )}
              </div>

              {message && (
                <div
                  className={`p-4 rounded-lg flex items-start gap-3 ${
                    messageType === "success"
                      ? "bg-green-50 border border-green-200"
                      : messageType === "error"
                        ? "bg-red-50 border border-red-200"
                        : "bg-blue-50 border border-blue-200"
                  }`}
                >
                  <div className="mt-0.5">
                    <MessageIcon />
                  </div>

                  <div className="flex-1">
                    <p
                      className={`text-sm font-medium ${
                        messageType === "success"
                          ? "text-green-700"
                          : messageType === "error"
                            ? "text-red-700"
                            : "text-blue-700"
                      }`}
                    >
                      {message}
                    </p>

                    {(uploading || processing) && (
                      <div className="mt-2 w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-1.5 rounded-full animate-pulse ${
                            uploading
                              ? "bg-blue-600 w-1/2"
                              : "bg-green-600 w-3/4"
                          }`}
                        ></div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {filename && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 text-green-700">
                    <FaCheckCircle />
                    <span className="font-semibold">Ready to process:</span>
                    <span className="text-sm">{filename}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {streamUrl && (
            <div className="bg-white rounded-xl shadow-sm p-6 mt-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                  <FaVideo className="text-red-500" />
                  Live Detection Feed
                </h2>

                <button
                  onClick={stopLive}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black transition text-sm font-medium"
                >
                  <FaStop />
                  Stop
                </button>
              </div>

              <img
                src={streamUrl}
                alt="Live processing"
                className="w-full rounded-lg border border-gray-200"
              />
              <p className="text-xs text-gray-400 mt-2">
                Boxes, IDs and counts are drawn on the GPU in real time. Click
                Stop to end the stream and free the server.
              </p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300 p-6">
            <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <MdVideoSettings className="text-blue-500" />
              How to Use
            </h3>

            <ol className="space-y-3 text-sm text-gray-600">
              {[
                "Select a traffic video file",
                "Choose road mode (One Way / Two Way)",
                "Click Upload to upload the video",
                "Click Watch Live to see detection in real time",
                "Click Stop to end the stream and upload a new video",
              ].map((step, index) => (
                <li key={step} className="flex items-start gap-2">
                  <span className="bg-blue-100 text-blue-600 font-bold rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0 text-xs">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300 p-6">
            <h3 className="text-lg font-bold text-slate-800 mb-3">
              System Status
            </h3>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-gray-500">Status</span>
                <span className="text-green-600 font-semibold flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full inline-block"></span>
                  Online
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-gray-500">Video</span>
                <span
                  className={
                    file
                      ? "text-blue-600 font-medium truncate"
                      : "text-gray-400"
                  }
                >
                  {file ? file.name : "None selected"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-gray-500">Road Mode</span>
                <span className="text-slate-700 font-medium">
                  {roadMode === "one_way" ? "One Way" : "Two Way"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-gray-500">Live Stream</span>
                <span
                  className={
                    streamUrl ? "text-red-600 font-medium" : "text-gray-400"
                  }
                >
                  {streamUrl ? "Running" : "Stopped"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-gray-500">Processing</span>
                <span
                  className={
                    processing ? "text-yellow-600 font-medium" : "text-gray-400"
                  }
                >
                  {processing ? "In progress..." : "Ready"}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h4 className="font-semibold text-blue-900 mb-2">💡 Tip</h4>
            <p className="text-xs text-blue-700">
              For best results, use videos with clear traffic flow, stable
              camera angle, and good lighting conditions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
