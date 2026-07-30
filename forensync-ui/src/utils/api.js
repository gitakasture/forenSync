/**
 * api.js - Centralised Axios instance for ForenSync.
 *
 * Import this wherever you need to call the Flask backend:
 *   import api from "../utils/api";
 *   const { data } = await api.post("/auth/login", payload);
 */

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api/v1",
  headers: { "Content-Type": "application/json" },
});

export default api;
