import axios from "axios";

// const API_BASE_URL = "http://127.0.0.1:8000";
// const API_BASE_URL = "http://100.48.43.71:8000";
const API_BASE_URL = "http://54.225.75.13:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export default api;
