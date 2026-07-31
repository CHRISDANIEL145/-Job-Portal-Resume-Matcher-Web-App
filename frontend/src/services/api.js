import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:5000/api";
const TOKEN_KEY = "alby_token";
const ROLE_KEY = "alby_role";
const LEGACY_TOKEN_KEY = "token";
const LEGACY_ROLE_KEY = "role";

const api = axios.create({
  baseURL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const requestUrl = error?.config?.url || "";
    const isAuthRoute = requestUrl.includes("/auth/login") || requestUrl.includes("/auth/register");

    if (status === 401 && !isAuthRoute) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(ROLE_KEY);
      localStorage.removeItem(LEGACY_TOKEN_KEY);
      localStorage.removeItem(LEGACY_ROLE_KEY);
      sessionStorage.setItem("auth_notice", "Session expired. Please login again.");
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
      error.normalizedMessage = "Session expired. Please login again.";
      return Promise.reject(error);
    }

    const data = error?.response?.data;
    let normalizedMessage = "";

    if (typeof data === "string") {
      if (data.includes("<html") || data.includes("<!DOCTYPE") || data.includes("<!doctype")) {
        normalizedMessage = `Server error (${status || "Unknown"}). Please try again later.`;
      } else {
        normalizedMessage = data;
      }
    } else if (data && typeof data === "object") {
      if (typeof data.error === "string") {
        normalizedMessage = data.error;
      } else if (data.error && typeof data.error.message === "string") {
        normalizedMessage = data.error.message;
      } else if (typeof data.message === "string") {
        normalizedMessage = data.message;
      } else if (typeof data.msg === "string") {
        normalizedMessage = data.msg;
      } else if (typeof data.detail === "string") {
        normalizedMessage = data.detail;
      }
    }

    if (!normalizedMessage) {
      if (error?.message && !error.message.toLowerCase().includes("status code")) {
        normalizedMessage = error.message;
      } else if (status) {
        normalizedMessage = `Request failed (${status}). Please check your input or try again.`;
      } else {
        normalizedMessage = "Network error. Please check your backend connection.";
      }
    }

    error.normalizedMessage = normalizedMessage;
    return Promise.reject(error);
  }
);

export default api;

