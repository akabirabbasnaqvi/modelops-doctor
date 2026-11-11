import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ErrorBoundary from "../ErrorBoundary";
import { addLogSink, type LogEntry } from "../../lib/logger";

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Kaboom while rendering");
  }

  return <p>Page content</p>;
}

describe("ErrorBoundary", () => {
  let entries: LogEntry[];
  let removeSink: () => void;

  beforeEach(() => {
    entries = [];
    removeSink = addLogSink((entry) => entries.push(entry));

    // React reports caught render errors to console.error; that noise is
    // expected here and would otherwise bury real failures.
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    removeSink();
  });

  it("renders its children when nothing throws", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Page content")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("replaces a crashed subtree with a fallback showing the error", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "This page failed to load" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Kaboom while rendering")).toBeInTheDocument();
    expect(screen.queryByText("Page content")).not.toBeInTheDocument();
  });

  it("reports the crash through the logger with the component stack", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );

    const report = entries.find(
      (entry) => entry.message === "Page failed to render",
    );

    expect(report).toBeDefined();
    expect(report?.level).toBe("error");
    expect(report?.error?.message).toBe("Kaboom while rendering");
    expect(report?.context?.componentStack).toEqual(
      expect.stringContaining("Bomb"),
    );
  });

  it("renders the children again after Try again once the cause is gone", async () => {
    const { rerender } = render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );

    rerender(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );

    // Still showing the fallback: the boundary holds the error until reset.
    expect(screen.getByRole("alert")).toBeInTheDocument();

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.getByText("Page content")).toBeInTheDocument();
  });

  it("clears the error when the reset key changes", () => {
    const { rerender } = render(
      <ErrorBoundary resetKey="/broken">
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();

    rerender(
      <ErrorBoundary resetKey="/somewhere-else">
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Page content")).toBeInTheDocument();
  });

  it("keeps the fallback when the reset key is unchanged", () => {
    const { rerender } = render(
      <ErrorBoundary resetKey="/broken">
        <Bomb shouldThrow />
      </ErrorBoundary>,
    );

    rerender(
      <ErrorBoundary resetKey="/broken">
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
