import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectsPage from "../ProjectsPage";
import { createProject, getProjects } from "../../api/projects";
import type { Project } from "../../types/project";

vi.mock("../../api/projects", () => ({
  getProjects: vi.fn(),
  createProject: vi.fn(),
}));

const mockedGetProjects = vi.mocked(getProjects);
const mockedCreateProject = vi.mocked(createProject);

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 1,
    name: "Customer Churn Monitoring",
    description: "Tracks churn model health",
    problem_type: "binary_classification",
    target_column: "churn",
    positive_class: "1",
    metric_priority: "f1",
    owner: "Akabir",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

async function fillRequiredFields() {
  const user = userEvent.setup();

  await user.type(screen.getByLabelText(/project name/i), "Fraud Monitoring");
  await user.type(screen.getByLabelText(/target column/i), "is_fraud");

  return user;
}

describe("ProjectsPage", () => {
  beforeEach(() => {
    mockedGetProjects.mockResolvedValue({ total: 0, projects: [] });
    mockedCreateProject.mockReset();
  });

  describe("loading existing projects", () => {
    it("renders the projects returned by the API", async () => {
      mockedGetProjects.mockResolvedValue({
        total: 1,
        projects: [makeProject()],
      });

      render(<ProjectsPage />);

      expect(
        await screen.findByText("Customer Churn Monitoring"),
      ).toBeInTheDocument();
      expect(screen.getByText("Tracks churn model health")).toBeInTheDocument();
    });

    it("shows an empty state when there are no projects", async () => {
      render(<ProjectsPage />);

      expect(
        await screen.findByText("No projects have been created."),
      ).toBeInTheDocument();
    });

    it("shows a fallback error when the request fails without a response", async () => {
      mockedGetProjects.mockRejectedValue(new Error("network down"));

      render(<ProjectsPage />);

      expect(
        await screen.findByText(/projects could not be loaded/i),
      ).toBeInTheDocument();
    });

    it("surfaces the backend error detail when loading fails", async () => {
      mockedGetProjects.mockRejectedValue({
        response: {
          status: 500,
          data: { detail: "Database connection pool exhausted." },
        },
      });

      render(<ProjectsPage />);

      expect(
        await screen.findByText("Database connection pool exhausted."),
      ).toBeInTheDocument();
    });

    it("falls back to placeholder text when a project has no description", async () => {
      mockedGetProjects.mockResolvedValue({
        total: 1,
        projects: [makeProject({ description: null, owner: null })],
      });

      render(<ProjectsPage />);

      expect(
        await screen.findByText("No project description was provided."),
      ).toBeInTheDocument();
      expect(screen.getByText("Not specified")).toBeInTheDocument();
    });
  });

  describe("creating a project", () => {
    it("submits the form and prepends the new project to the list", async () => {
      mockedGetProjects.mockResolvedValue({
        total: 1,
        projects: [makeProject({ id: 1, name: "Existing Project" })],
      });

      mockedCreateProject.mockResolvedValue(
        makeProject({ id: 2, name: "Fraud Monitoring" }),
      );

      render(<ProjectsPage />);

      await screen.findByText("Existing Project");

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /create project/i }));

      await waitFor(() => {
        expect(mockedCreateProject).toHaveBeenCalledTimes(1);
      });

      expect(mockedCreateProject).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Fraud Monitoring",
          target_column: "is_fraud",
          problem_type: "binary_classification",
          metric_priority: "f1",
        }),
      );

      const projectsSection = screen
        .getByRole("heading", { name: /registered projects/i })
        .closest("section") as HTMLElement;

      const headings = within(projectsSection).getAllByRole("heading", {
        level: 3,
      });

      expect(headings[0]).toHaveTextContent("Fraud Monitoring");
    });

    it("normalises blank optional fields to null", async () => {
      mockedCreateProject.mockResolvedValue(makeProject({ id: 2 }));

      render(<ProjectsPage />);

      await screen.findByText("No projects have been created.");

      const user = await fillRequiredFields();

      await user.clear(screen.getByLabelText(/positive class/i));
      await user.click(screen.getByRole("button", { name: /create project/i }));

      await waitFor(() => {
        expect(mockedCreateProject).toHaveBeenCalledWith(
          expect.objectContaining({
            description: null,
            positive_class: null,
            owner: null,
          }),
        );
      });
    });

    it("confirms the project was created", async () => {
      mockedCreateProject.mockResolvedValue(
        makeProject({ id: 2, name: "Fraud Monitoring" }),
      );

      render(<ProjectsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /create project/i }));

      expect(
        await screen.findByText(
          'Project "Fraud Monitoring" was created successfully.',
        ),
      ).toBeInTheDocument();
    });

    it("surfaces the API error detail when creation fails", async () => {
      mockedCreateProject.mockRejectedValue({
        response: { data: { detail: "A project named 'X' already exists." } },
      });

      render(<ProjectsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /create project/i }));

      expect(
        await screen.findByText("A project named 'X' already exists."),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedCreateProject.mockRejectedValue(new Error("boom"));

      render(<ProjectsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /create project/i }));

      expect(
        await screen.findByText("The project could not be created."),
      ).toBeInTheDocument();
    });

    it("clears the form after a successful submission", async () => {
      mockedCreateProject.mockResolvedValue(makeProject({ id: 2 }));

      render(<ProjectsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /create project/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/project name/i)).toHaveValue("");
      });

      expect(screen.getByLabelText(/target column/i)).toHaveValue("");
    });
  });
});
