import axios from "axios";

import { logError, type LogContext } from "../lib/logger";

const apiBaseUrl =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
});

/**
 * Pull the parts of a failed request worth logging. Deliberately excludes
 * the request body and headers so form data and any future auth tokens
 * never end up in logs.
 */
export function describeFailedRequest(error: unknown): LogContext | undefined {
  if (!axios.isAxiosError(error)) {
    return undefined;
  }

  return {
    method: error.config?.method?.toUpperCase(),
    url: error.config?.url,
    status: error.response?.status,
    code: error.code,
  };
}

export function reportFailedRequest(error: unknown): Promise<never> {
  logError("API request failed", error, describeFailedRequest(error));

  return Promise.reject(error);
}

api.interceptors.response.use((response) => response, reportFailedRequest);
