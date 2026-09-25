import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HealthChecksPage from "../HealthChecksPage";
import {
  getDiagnosisReport,
  getLatestHealthCheck,
  runHealthCheck,
} from "../../api/healthChecks";
import type { DiagnosisReport, HealthCheck } from "../../api/healthChecks";

vi.mock("../../api/healthChecks", () => ({
  getLatestHealthCheck: vi.fn(),
  getDiagnosisReport: vi.fn(),
  runHealthCheck: vi.fn(),
}));

const mockedGetLatest = vi.mocked(getLatestHealthCheck);
const mockedGetReport = vi.mocked(getDiagnosisReport);
const mockedRunHealthCheck = vi.mocked(runHealthCheck);

function makeHealthCheck(overrides: Partial<HealthCheck> = {}): HealthCheck {
  return {
    id: 11,
    project_id: 1,
    model_version_id: 1,
    baseline_dataset_id: 1,
    prediction_batch_id: 1,
    status: "completed",
    health_score: 79.55,
    metrics: { accuracy: 0.9, f1: 0.833, average_confidence: 0.812 },
    drift: { drift_rate: 0.6 },
    component_scores: { performance_score: 88.5, drift_score: 40 },
    missing_rate: 0,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeReport(overrides: Partial<DiagnosisReport> = {}): DiagnosisReport {
  return {
    id: 5,
    health_check_id: 11,
    summary: "The model shows meaningful drift and needs review.",
    risk_level: "high",
    retraining_recommended: true,
    findings: [
      { code: "DRIFT_HIGH", severity: "high", message: "3 features drifted." },
    ],
    recommendations: ["Retrain on recent production data."],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("HealthChecksPage", () => {
  beforeEach(() => {
    mockedGetLatest.mockReset();
    mockedGetReport.mockReset();
    mockedRunHealthCheck.mockReset();
  });

  describe("loading the latest health check", () => {
    it("requests the report for the health check it just loaded", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck({ id: 42 }));
      mockedGetReport.mockResolvedValue(makeReport({ health_check_id: 42 }));

      render(<HealthChecksPage />);

      await waitFor(() => {
        expect(mockedGetLatest).toHaveBeenCalledWith(1);
      });

      expect(mockedGetReport).toHaveBeenCalledWith(42);
    });

    it("renders the headline metrics", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck());
      mockedGetReport.mockResolvedValue(makeReport());

      render(<HealthChecksPage />);

      expect(await screen.findByText("79.55")).toBeInTheDocument();
      expect(screen.getByText("0.900")).toBeInTheDocument();
      expect(screen.getByText("0.833")).toBeInTheDocument();
      expect(screen.getByText("60%")).toBeInTheDocument();
      expect(screen.getByText("0.812")).toBeInTheDocument();
    });

    it("shows N/A for metrics the API did not return", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck({ metrics: {} }));
      mockedGetReport.mockResolvedValue(makeReport());

      render(<HealthChecksPage />);

      await waitFor(() => {
        expect(screen.getAllByText("N/A")).toHaveLength(3);
      });
    });

    it("humanises component score labels", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck());
      mockedGetReport.mockResolvedValue(makeReport());

      render(<HealthChecksPage />);

      expect(await screen.findByText("Performance Score")).toBeInTheDocument();
      expect(screen.getByText("Drift Score")).toBeInTheDocument();
      expect(screen.getByText("88.5")).toBeInTheDocument();
    });

    it("renders findings and recommendations from the report", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck());
      mockedGetReport.mockResolvedValue(makeReport());

      render(<HealthChecksPage />);

      expect(
        await screen.findByText(/model shows meaningful drift/i),
      ).toBeInTheDocument();
      expect(screen.getByText("high")).toBeInTheDocument();
      expect(screen.getByText("Yes")).toBeInTheDocument();
      expect(screen.getByText(/3 features drifted/)).toBeInTheDocument();
      expect(
        screen.getByText("Retrain on recent production data."),
      ).toBeInTheDocument();
    });

    it("reports No when retraining is not recommended", async () => {
      mockedGetLatest.mockResolvedValue(makeHealthCheck());
      mockedGetReport.mockResolvedValue(
        makeReport({ retraining_recommended: false }),
      );

      render(<HealthChecksPage />);

      expect(await screen.findByText("No")).toBeInTheDocument();
    });

    it("shows an error when no health check exists yet", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));

      render(<HealthChecksPage />);

      expect(
        await screen.findByText("No health check could be loaded."),
      ).toBeInTheDocument();
    });
  });

  describe("running a health check on demand", () => {
    it("passes the project and pipeline ids to the API", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));
      mockedRunHealthCheck.mockResolvedValue({
        health_check: makeHealthCheck(),
        diagnosis_report: makeReport(),
      });

      render(<HealthChecksPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /run health check/i }),
      );

      await waitFor(() => {
        expect(mockedRunHealthCheck).toHaveBeenCalledWith(1, 1, 1, 1);
      });
    });

    it("renders the results returned by the run", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));
      mockedRunHealthCheck.mockResolvedValue({
        health_check: makeHealthCheck({ health_score: 91.2 }),
        diagnosis_report: makeReport({ summary: "The model is healthy." }),
      });

      render(<HealthChecksPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /run health check/i }),
      );

      expect(await screen.findByText("91.20")).toBeInTheDocument();
      expect(screen.getByText("The model is healthy.")).toBeInTheDocument();
    });

    it("re-enables the button after the run finishes", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));
      mockedRunHealthCheck.mockResolvedValue({
        health_check: makeHealthCheck(),
        diagnosis_report: makeReport(),
      });

      render(<HealthChecksPage />);

      const user = userEvent.setup();
      const button = screen.getByRole("button", { name: /run health check/i });

      await user.click(button);

      await waitFor(() => {
        expect(button).toBeEnabled();
      });

      expect(button).toHaveTextContent("Run Health Check");
    });

    it("surfaces the API error detail when the run fails", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));
      mockedRunHealthCheck.mockRejectedValue({
        response: { data: { detail: "Baseline dataset is missing." } },
      });

      render(<HealthChecksPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /run health check/i }),
      );

      expect(
        await screen.findByText("Baseline dataset is missing."),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedGetLatest.mockRejectedValue(new Error("not found"));
      mockedRunHealthCheck.mockRejectedValue(new Error("boom"));

      render(<HealthChecksPage />);

      const user = userEvent.setup();

      await user.click(
        screen.getByRole("button", { name: /run health check/i }),
      );

      expect(
        await screen.findByText("The health check failed."),
      ).toBeInTheDocument();
    });
  });
});
