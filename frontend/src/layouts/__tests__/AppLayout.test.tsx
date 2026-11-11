import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AppLayout from "../AppLayout";

function BrokenPage(): never {
  throw new Error("Broken page");
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<p>Dashboard content</p>} />
          <Route path="/projects" element={<p>Projects content</p>} />
          <Route path="/broken" element={<BrokenPage />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppLayout", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders every navigation link", () => {
    renderAt("/");

    for (const label of [
      "Dashboard",
      "Projects",
      "Model Registry",
      "Datasets",
      "Prediction Logs",
      "Model Health",
      "Automation Jobs",
    ]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
  });

  it("renders the matched route in the content area", () => {
    renderAt("/projects");

    expect(screen.getByText("Projects content")).toBeInTheDocument();
  });

  it("marks the current route's link as active", () => {
    renderAt("/projects");

    expect(screen.getByRole("link", { name: "Projects" })).toHaveClass(
      "active",
    );
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveClass(
      "active",
    );
  });

  it("opens and closes the mobile navigation", async () => {
    renderAt("/");

    const user = userEvent.setup();
    const sidebar = screen.getByRole("complementary");

    expect(sidebar).not.toHaveClass("sidebar-open");

    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    expect(sidebar).toHaveClass("sidebar-open");

    // Both the close button and the overlay are labelled "Close navigation".
    const [closeButton] = screen.getAllByRole("button", {
      name: "Close navigation",
    });

    await user.click(closeButton);
    expect(sidebar).not.toHaveClass("sidebar-open");
  });

  describe("when a page crashes while rendering", () => {
    it("contains the failure and keeps the navigation usable", () => {
      renderAt("/broken");

      expect(
        screen.getByRole("heading", { name: "This page failed to load" }),
      ).toBeInTheDocument();

      // The sidebar survived: before the boundary, the whole tree unmounted.
      expect(
        screen.getByRole("link", { name: "Dashboard" }),
      ).toBeInTheDocument();
    });

    it("recovers when the user navigates to another page", async () => {
      renderAt("/broken");

      await userEvent
        .setup()
        .click(screen.getByRole("link", { name: "Dashboard" }));

      expect(screen.getByText("Dashboard content")).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", { name: "This page failed to load" }),
      ).not.toBeInTheDocument();
    });
  });
});
