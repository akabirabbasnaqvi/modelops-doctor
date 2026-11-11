import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RecentJobsTable from "../RecentJobsTable";

describe("RecentJobsTable", () => {
  it("renders each job's ID, type and status in the supplied order", () => {
    render(
      <RecentJobsTable
        jobs={[
          { id: 9, job_type: "health_check", status: "completed" },
          { id: 3, job_type: "profile", status: "failed" },
        ]}
      />,
    );

    const [, firstJob, secondJob] = screen.getAllByRole("row");
    expect(
      within(firstJob)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["9", "health_check", "completed"]);
    expect(
      within(secondJob)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["3", "profile", "failed"]);
  });

  it("keeps the column headers when there are no jobs", () => {
    render(<RecentJobsTable jobs={[]} />);

    expect(
      screen.getAllByRole("columnheader").map((cell) => cell.textContent),
    ).toEqual(["ID", "Type", "Status"]);
    expect(screen.getAllByRole("row")).toHaveLength(1);
    expect(screen.queryByRole("cell")).not.toBeInTheDocument();
  });
});
