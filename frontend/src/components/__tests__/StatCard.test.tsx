import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import StatCard from "../StatCard";

describe("StatCard", () => {
  it("renders a zero count and updates when the data changes", () => {
    const { rerender } = render(<StatCard title="Models" value={0} />);

    expect(screen.getByRole("heading", { name: "Models" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "0" })).toBeVisible();

    rerender(<StatCard title="Models" value={12} />);

    expect(screen.getByRole("heading", { name: "12" })).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "0" }),
    ).not.toBeInTheDocument();
  });

  it("renders a formatted string value", () => {
    render(<StatCard title="Success rate" value="98.5%" />);

    expect(screen.getByRole("heading", { name: "98.5%" })).toBeVisible();
  });
});
