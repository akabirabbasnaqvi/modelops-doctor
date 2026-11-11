import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  addLogSink,
  logError,
  logInfo,
  logWarning,
  serializeError,
  type LogEntry,
} from "../logger";

describe("logger", () => {
  let entries: LogEntry[];
  let removeSink: () => void;

  beforeEach(() => {
    entries = [];
    removeSink = addLogSink((entry) => entries.push(entry));

    // Keep the default console sink quiet during tests.
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.spyOn(console, "info").mockImplementation(() => {});
  });

  afterEach(() => {
    removeSink();
  });

  it("emits a structured error entry with an ISO timestamp", () => {
    logError("Upload failed", new TypeError("bad input"), { page: "datasets" });

    expect(entries).toHaveLength(1);

    const [entry] = entries;

    expect(entry.level).toBe("error");
    expect(entry.message).toBe("Upload failed");
    expect(entry.context).toEqual({ page: "datasets" });
    expect(entry.error).toMatchObject({
      name: "TypeError",
      message: "bad input",
    });
    expect(new Date(entry.timestamp).toISOString()).toBe(entry.timestamp);
  });

  it("omits error and context when none are given", () => {
    logInfo("Dashboard loaded");

    expect(entries[0]).not.toHaveProperty("error");
    expect(entries[0]).not.toHaveProperty("context");
  });

  it("emits warnings at warn level", () => {
    logWarning("Slow response", { durationMs: 4200 });

    expect(entries[0]).toMatchObject({
      level: "warn",
      context: { durationMs: 4200 },
    });
  });

  it("still writes to the console by default", () => {
    logError("Something broke");

    expect(console.error).toHaveBeenCalledWith(
      "[error] Something broke",
      expect.objectContaining({ level: "error" }),
    );
  });

  it("keeps delivering to other sinks when one throws", () => {
    const removeBroken = addLogSink(() => {
      throw new Error("tracker offline");
    });

    expect(() => logError("Still reported")).not.toThrow();
    expect(entries).toHaveLength(1);

    removeBroken();
  });

  it("stops delivering to a sink once it is removed", () => {
    removeSink();
    logError("After removal");

    expect(entries).toHaveLength(0);
  });

  describe("serializeError", () => {
    it("keeps the name, message and stack of an Error", () => {
      const error = new RangeError("out of range");

      expect(serializeError(error)).toEqual({
        name: "RangeError",
        message: "out of range",
        stack: error.stack,
      });
    });

    it("wraps a thrown string", () => {
      expect(serializeError("boom")).toEqual({
        name: "Error",
        message: "boom",
      });
    });

    it("stringifies a thrown plain object", () => {
      expect(serializeError({ code: 500 })).toEqual({
        name: "NonErrorThrown",
        message: '{"code":500}',
      });
    });

    it("falls back to String() for values JSON cannot encode", () => {
      const circular: Record<string, unknown> = {};
      circular.self = circular;

      expect(serializeError(circular)).toEqual({
        name: "NonErrorThrown",
        message: "[object Object]",
      });
    });

    it("returns undefined for null and undefined", () => {
      expect(serializeError(null)).toBeUndefined();
      expect(serializeError(undefined)).toBeUndefined();
    });
  });
});
