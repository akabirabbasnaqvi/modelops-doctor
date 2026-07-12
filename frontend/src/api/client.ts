import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000/api/v1";

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API request failed:", error);

    return Promise.reject(error);
  }
);