import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { describeFailedRequest, reportFailedRequest } from "../client";
import { addLogSink, type LogEntry } from "../../lib/logger";

// axios.isAxiosError only checks this flag, so a plain object stands in for
// a real AxiosError without needing a live request.
function axiosError(overrides: Record<string, unknown> = {}) {
  return {
    isAxiosError: true,
    name: "AxiosError",
    message: "Request failed with status code 500",
    code: "ERR_BAD_RESPONSE",
    config: {
      method: "post",
      url: "/projects",
      data: '{"name":"secret payload"}',
      headers: { Authorization: "Bearer should-never-be-logged" },
    },
    response: { status: 500, data: { detail: "boom" } },
    ...overrides,
  };
}

describe("API client error reporting", () => {
  let entries: LogEntry[];
  let removeSink: () => void;

  beforeEach(() => {
    entries = [];
    removeSink = addLogSink((entry) => entries.push(entry));
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    removeSink();
  });

  describe("describeFailedRequest", () => {
    it("extracts method, url, status and code", () => {
      expect(describeFailedRequest(axiosError())).toEqual({
        method: "POST",
        url: "/projects",
        status: 500,
        code: "ERR_BAD_RESPONSE",
      });
    });

    it("never includes the request body or headers", () => {
      const context = describeFailedRequest(axiosError());
      const serialized = JSON.stringify(context);

      expect(serialized).not.toContain("secret payload");
      expect(serialized).not.toContain("should-never-be-logged");
    });

    it("leaves status undefined for network errors with no response", () => {
      const context = describeFailedRequest(
        axiosError({ response: undefined, code: "ERR_NETWORK" }),
      );

      expect(context).toMatchObject({ status: undefined, code: "ERR_NETWORK" });
    });

    it("returns undefined for errors that did not come from axios", () => {
      expect(describeFailedRequest(new Error("not axios"))).toBeUndefined();
    });
  });

  describe("reportFailedRequest", () => {
    it("logs the failure with request context", async () => {
      await expect(reportFailedRequest(axiosError())).rejects.toBeDefined();

      expect(entries).toHaveLength(1);
      expect(entries[0]).toMatchObject({
        level: "error",
        message: "API request failed",
        context: { method: "POST", url: "/projects", status: 500 },
      });
    });

    it("re-rejects with the original error so callers can handle it", async () => {
      const error = axiosError();

      await expect(reportFailedRequest(error)).rejects.toBe(error);
    });
  });
});
