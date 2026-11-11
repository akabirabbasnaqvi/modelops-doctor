/**
 * Structured client-side logging.
 *
 * Every error the frontend reports goes through here as a LogEntry rather
 * than an ad-hoc console call, so there is one place to attach an error
 * tracker. Register one with addLogSink(); the console sink stays on by
 * default so local development is unchanged.
 */

export type LogLevel = "error" | "warn" | "info";

export type LogContext = Record<string, unknown>;

export type SerializedError = {
  name: string;
  message: string;
  stack?: string;
};

export type LogEntry = {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: LogContext;
  error?: SerializedError;
};

export type LogSink = (entry: LogEntry) => void;

const consoleSink: LogSink = (entry) => {
  const method = entry.level === "info" ? "info" : entry.level;

  console[method](`[${entry.level}] ${entry.message}`, entry);
};

const sinks = new Set<LogSink>([consoleSink]);

/** Register a sink. Returns a function that removes it again. */
export function addLogSink(sink: LogSink): () => void {
  sinks.add(sink);

  return () => {
    sinks.delete(sink);
  };
}

/** Normalise anything that was thrown into a plain, serialisable shape. */
export function serializeError(error: unknown): SerializedError | undefined {
  if (error === undefined || error === null) {
    return undefined;
  }

  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
    };
  }

  if (typeof error === "string") {
    return { name: "Error", message: error };
  }

  try {
    return { name: "NonErrorThrown", message: JSON.stringify(error) };
  } catch {
    return { name: "NonErrorThrown", message: String(error) };
  }
}

function emit(entry: LogEntry): void {
  for (const sink of sinks) {
    try {
      sink(entry);
    } catch {
      // A failing sink must never take down the app or the other sinks.
    }
  }
}

function log(
  level: LogLevel,
  message: string,
  error?: unknown,
  context?: LogContext,
): void {
  emit({
    level,
    message,
    timestamp: new Date().toISOString(),
    ...(context && { context }),
    ...(error !== undefined && { error: serializeError(error) }),
  });
}

export function logError(
  message: string,
  error?: unknown,
  context?: LogContext,
): void {
  log("error", message, error, context);
}

export function logWarning(message: string, context?: LogContext): void {
  log("warn", message, undefined, context);
}

export function logInfo(message: string, context?: LogContext): void {
  log("info", message, undefined, context);
}
