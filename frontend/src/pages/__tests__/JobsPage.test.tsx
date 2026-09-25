import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import JobsPage from "../JobsPage";
import { getJobs, queueHealthCheck } from "../../api/jobs";
import type { AutomationJob } from "../../api/jobs";

vi.mock("../../api/jobs", () => ({
  getJobs: vi.fn(),
  queueHealthCheck: vi.fn(),
}));

const mockedGetJobs = vi.mocked(getJobs);
const mockedQueueHealthCheck = vi.mocked(queueHealthCheck);

function makeJob(overrides: Partial<AutomationJob> = {}): AutomationJob {
  return {
    id: 9,
    project_id: 1,
    job_type: "health_check",
    status: "completed",
    celery_task_id: "abc-123",
    payload: {},
    result: { health_score: 79.55 },
    error_message: null,
    created_at: "2026-01-01T00:00:00Z",
    started_at: "2026-01-01T00:00:01Z",
    finished_at: "2026-01-01T00:00:09Z",
    ...overrides,
  };
}

describe("JobsPage", () => {
  beforeEach(() => {
    mockedGetJobs.mockResolvedValue({ total: 0, jobs: [] });
    mockedQueueHealthCheck.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("listing jobs", () => {
    it("renders a job as a table row", async () => {
      mockedGetJobs.mockResolvedValue({ total: 1, jobs: [makeJob()] });

      render(<JobsPage />);

      const row = (await screen.findByText("health_check")).closest(
        "tr",
      ) as HTMLElement;

      expect(within(row).getByText("9")).toBeInTheDocument();
      expect(within(row).getByText("completed")).toBeInTheDocument();
      expect(within(row).getByText("79.55")).toBeInTheDocument();
    });

    it("shows N/A when a job has no health score yet", async () => {
      mockedGetJobs.mockResolvedValue({
        total: 1,
        jobs: [makeJob({ status: "queued", result: {} })],
      });

      render(<JobsPage />);

      expect(await screen.findByText("N/A")).toBeInTheDocument();
    });

    it("shows a dash when a job has no error message", async () => {
      mockedGetJobs.mockResolvedValue({ total: 1, jobs: [makeJob()] });

      render(<JobsPage />);

      expect(await screen.findByText("—")).toBeInTheDocument();
    });

    it("renders the failure reason for a failed job", async () => {
      mockedGetJobs.mockResolvedValue({
        total: 1,
        jobs: [
          makeJob({
            status: "failed",
            result: {},
            error_message: "Baseline dataset is missing.",
          }),
        ],
      });

      render(<JobsPage />);

      expect(
        await screen.findByText("Baseline dataset is missing."),
      ).toBeInTheDocument();
    });

    it("shows an error when jobs cannot be loaded", async () => {
      mockedGetJobs.mockRejectedValue(new Error("network down"));

      render(<JobsPage />);

      expect(
        await screen.findByText("Automation jobs could not be loaded."),
      ).toBeInTheDocument();
    });

    it("polls for new jobs on an interval", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });

      render(<JobsPage />);

      await waitFor(() => {
        expect(mockedGetJobs).toHaveBeenCalledTimes(1);
      });

      await vi.advanceTimersByTimeAsync(5000);

      expect(mockedGetJobs).toHaveBeenCalledTimes(2);
    });
  });

  describe("queueing a health check", () => {
    it("queues the job and refreshes the list", async () => {
      mockedQueueHealthCheck.mockResolvedValue({ job_id: 10 });

      render(<JobsPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /queue health check/i }),
      );

      await waitFor(() => {
        expect(mockedQueueHealthCheck).toHaveBeenCalledWith(1);
      });

      // once on mount, once after queueing
      expect(mockedGetJobs).toHaveBeenCalledTimes(2);
    });

    it("re-enables the button once queueing finishes", async () => {
      mockedQueueHealthCheck.mockResolvedValue({ job_id: 10 });

      render(<JobsPage />);

      const user = userEvent.setup();
      const button = screen.getByRole("button", {
        name: /queue health check/i,
      });

      await user.click(button);

      await waitFor(() => {
        expect(button).toBeEnabled();
      });

      expect(button).toHaveTextContent("Queue Health Check");
    });

    it("surfaces the API error detail when queueing fails", async () => {
      mockedQueueHealthCheck.mockRejectedValue({
        response: { data: { detail: "Celery broker is unreachable." } },
      });

      render(<JobsPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /queue health check/i }),
      );

      expect(
        await screen.findByText("Celery broker is unreachable."),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedQueueHealthCheck.mockRejectedValue(new Error("boom"));

      render(<JobsPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /queue health check/i }),
      );

      expect(
        await screen.findByText("The background task could not be queued."),
      ).toBeInTheDocument();
    });
  });
});
