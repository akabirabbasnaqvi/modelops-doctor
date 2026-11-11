import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "../App";

vi.mock("../pages/DashboardPage", () => ({
  default: () => <h1>Dashboard page</h1>,
}));
vi.mock("../pages/ProjectsPage", () => ({
  default: () => <h1>Projects page</h1>,
}));
vi.mock("../pages/ModelsPage", () => ({ default: () => <h1>Models page</h1> }));
vi.mock("../pages/DatasetsPage", () => ({
  default: () => <h1>Datasets page</h1>,
}));
vi.mock("../pages/PredictionBatchesPage", () => ({
  default: () => <h1>Predictions page</h1>,
}));
vi.mock("../pages/HealthChecksPage", () => ({
  default: () => <h1>Health page</h1>,
}));
vi.mock("../pages/JobsPage", () => ({ default: () => <h1>Jobs page</h1> }));

describe("App routes", () => {
  it.each([
    ["/", "Dashboard page"],
    ["/projects", "Projects page"],
    ["/models", "Models page"],
    ["/datasets", "Datasets page"],
    ["/predictions", "Predictions page"],
    ["/health", "Health page"],
    ["/jobs", "Jobs page"],
  ])("renders %s through the application layout", (path, heading) => {
    window.history.replaceState({}, "", path);

    render(<App />);

    expect(screen.getByRole("heading", { name: heading })).toBeVisible();
    expect(screen.getByRole("link", { name: "Projects" })).toBeVisible();
  });
});
