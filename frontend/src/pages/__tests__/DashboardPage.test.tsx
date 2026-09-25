import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "../DashboardPage";
import { getDashboard } from "../../api/dashboard";

vi.mock("../../api/dashboard", () => ({
  getDashboard: vi.fn(),
}));

// recharts measures its container, which jsdom reports as 0x0, so the chart
// never renders. Stubbing it keeps this suite about the dashboard itself.
vi.mock("../../components/DriftChart", () => ({
  default: ({ driftedFeatures }: { driftedFeatures: string[] }) => (
    <div data-testid="drift-chart">{driftedFeatures.join(", ")}</div>
  ),
}));

const mockedGetDashboard = vi.mocked(getDashboard);

function makeDashboard(overrides: Record<string, unknown> = {}) {
  return {
    project_id: 1,
    project_name: "Customer Churn Monitoring",
    counts: {
      models: 3,
      datasets: 4,
      prediction_batches: 5,
      health_checks: 6,
    },
    latest_health: {
      health_check_id: 11,
      health_score: 79.55,
      status: "completed",
      risk_level: "high",
      retraining_recommended: true,
      drifted_features: ["age", "tenure_months"],
      recommendations: ["Retrain on recent data."],
    },
    recent_jobs: [
      {
        id: 9,
        job_type: "health_check",
        status: "completed",
        created_at: "2026-01-01T00:00:00Z",
        finished_at: "2026-01-01T00:01:00Z",
      },
    ],
    ...overrides,
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    mockedGetDashboard.mockReset();
  });

  it("shows a loading state before the request resolves", () => {
    mockedGetDashboard.mockReturnValue(new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getByText("Loading dashboard...")).toBeInTheDocument();
  });

  it("requests the dashboard for the active project", async () => {
    mockedGetDashboard.mockResolvedValue(makeDashboard());

    render(<DashboardPage />);

    await waitFor(() => {
      expect(mockedGetDashboard).toHaveBeenCalledWith(1);
    });
  });

  it("renders the project name and entity counts", async () => {
    mockedGetDashboard.mockResolvedValue(makeDashboard());

    render(<DashboardPage />);

    expect(
      await screen.findByRole("heading", {
        name: "Customer Churn Monitoring",
      }),
    ).toBeInTheDocument();

    for (const [label, value] of [
      ["Models", "3"],
      ["Datasets", "4"],
      ["Prediction Batches", "5"],
      ["Health Checks", "6"],
    ]) {
      const card = screen.getByText(label).closest("div") as HTMLElement;

      expect(within(card).getByText(value)).toBeInTheDocument();
    }
  });

  it("renders the latest health summary", async () => {
    mockedGetDashboard.mockResolvedValue(makeDashboard());

    render(<DashboardPage />);

    expect(await screen.findByText("79.55")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
  });

  it("reports No when retraining is not recommended", async () => {
    mockedGetDashboard.mockResolvedValue(
      makeDashboard({
        latest_health: {
          ...makeDashboard().latest_health,
          retraining_recommended: false,
        },
      }),
    );

    render(<DashboardPage />);

    expect(await screen.findByText("No")).toBeInTheDocument();
  });

  it("falls back to placeholders when no health check exists", async () => {
    mockedGetDashboard.mockResolvedValue(
      makeDashboard({ latest_health: null }),
    );

    render(<DashboardPage />);

    expect(
      await screen.findByText("No health check available"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Not available")).toHaveLength(2);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders recent jobs in a table", async () => {
    mockedGetDashboard.mockResolvedValue(makeDashboard());

    render(<DashboardPage />);

    const row = (await screen.findByText("health_check")).closest(
      "tr",
    ) as HTMLElement;

    expect(within(row).getByText("9")).toBeInTheDocument();
    expect(within(row).getByText("completed")).toBeInTheDocument();
  });

  it("passes the drifted features to the chart", async () => {
    mockedGetDashboard.mockResolvedValue(makeDashboard());

    render(<DashboardPage />);

    expect(await screen.findByTestId("drift-chart")).toHaveTextContent(
      "age, tenure_months",
    );
  });

  it("shows an error when the dashboard cannot be loaded", async () => {
    mockedGetDashboard.mockRejectedValue(new Error("backend down"));

    render(<DashboardPage />);

    expect(
      await screen.findByRole("heading", { name: "Dashboard unavailable" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/confirm that the fastapi backend is running/i),
    ).toBeInTheDocument();
  });
});
