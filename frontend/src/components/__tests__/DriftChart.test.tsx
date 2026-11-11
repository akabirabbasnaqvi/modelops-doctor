import { render, screen, within } from "@testing-library/react";
import { cloneElement, type ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import DriftChart from "../DriftChart";

// jsdom has no layout engine. Give the real chart fixed dimensions instead
// of relying on ResponsiveContainer's browser-only size measurements.
vi.mock("recharts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("recharts")>()),
  ResponsiveContainer: ({
    children,
  }: {
    children: ReactElement<{ width?: number; height?: number }>;
  }) => cloneElement(children, { width: 640, height: 300 }),
}));

describe("DriftChart", () => {
  it("renders the feature names on the chart and updates them", () => {
    const { rerender } = render(
      <DriftChart driftedFeatures={["age", "monthly_charges"]} />,
    );

    const chart = within(screen.getByRole("application"));
    expect(chart.getByText("age")).toBeInTheDocument();
    expect(chart.getByText("monthly_charges")).toBeInTheDocument();

    rerender(<DriftChart driftedFeatures={["tenure_months"]} />);

    expect(chart.getByText("tenure_months")).toBeInTheDocument();
    expect(chart.queryByText("age")).not.toBeInTheDocument();
    expect(chart.queryByText("monthly_charges")).not.toBeInTheDocument();
  });

  it("renders an empty chart without inventing drifted features", () => {
    const { container } = render(<DriftChart driftedFeatures={[]} />);

    expect(container.querySelector("svg")).toBeInTheDocument();
    expect(
      container.querySelectorAll(
        ".recharts-xAxis .recharts-cartesian-axis-tick",
      ),
    ).toHaveLength(0);
  });
});
