import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HealthGauge from "../HealthGauge";

describe("HealthGauge", () => {
  it.each([
    [0, "#ef4444"],
    [59.9, "#ef4444"],
    [60, "#f59e0b"],
    [79.9, "#f59e0b"],
    [80, "#22c55e"],
    [100, "#22c55e"],
  ])("renders score %s with the matching health color", (score, color) => {
    render(<HealthGauge score={score} />);

    expect(screen.getByRole("heading", { name: "Health Score" })).toBeVisible();
    expect(screen.getByText(String(score))).toHaveStyle({ borderColor: color });
  });
});
