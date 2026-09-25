import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ModelsPage from "../ModelsPage";
import { getModels, registerModel } from "../../api/models";
import type { ModelVersion } from "../../api/models";

vi.mock("../../api/models", () => ({
  getModels: vi.fn(),
  registerModel: vi.fn(),
}));

const mockedGetModels = vi.mocked(getModels);
const mockedRegisterModel = vi.mocked(registerModel);

function makeModel(overrides: Partial<ModelVersion> = {}): ModelVersion {
  return {
    id: 1,
    project_id: 1,
    name: "Customer Churn Classifier",
    version: "1.0.0",
    algorithm: "Random Forest",
    framework: "scikit-learn",
    metrics: { accuracy: 0.9, precision: 0.86, recall: 0.81, f1: 0.83 },
    artifact_uri: null,
    status: "registered",
    training_date: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

async function fillRequiredFields() {
  const user = userEvent.setup();

  await user.type(screen.getByLabelText(/model name/i), "Fraud Classifier");
  await user.type(screen.getByLabelText(/algorithm/i), "XGBoost");

  return user;
}

describe("ModelsPage", () => {
  beforeEach(() => {
    mockedGetModels.mockResolvedValue({ total: 0, models: [] });
    mockedRegisterModel.mockReset();
  });

  describe("loading registered versions", () => {
    it("requests models for the active project", async () => {
      render(<ModelsPage />);

      await waitFor(() => {
        expect(mockedGetModels).toHaveBeenCalledWith(1);
      });
    });

    it("renders each model as a table row", async () => {
      mockedGetModels.mockResolvedValue({
        total: 1,
        models: [makeModel()],
      });

      render(<ModelsPage />);

      const row = (
        await screen.findByText("Customer Churn Classifier")
      ).closest("tr") as HTMLElement;

      expect(within(row).getByText("1.0.0")).toBeInTheDocument();
      expect(within(row).getByText("Random Forest")).toBeInTheDocument();
      expect(within(row).getByText("scikit-learn")).toBeInTheDocument();
      expect(within(row).getByText("registered")).toBeInTheDocument();
    });

    it("formats the f1 metric to three decimal places", async () => {
      mockedGetModels.mockResolvedValue({
        total: 1,
        models: [makeModel({ metrics: { f1: 0.8312 } })],
      });

      render(<ModelsPage />);

      expect(await screen.findByText("0.831")).toBeInTheDocument();
    });

    it("shows N/A when a model has no f1 metric", async () => {
      mockedGetModels.mockResolvedValue({
        total: 1,
        models: [makeModel({ metrics: {} })],
      });

      render(<ModelsPage />);

      expect(await screen.findByText("N/A")).toBeInTheDocument();
    });

    it("shows a fallback error when the request fails without a response", async () => {
      mockedGetModels.mockRejectedValue(new Error("network down"));

      render(<ModelsPage />);

      expect(
        await screen.findByText("Model versions could not be loaded."),
      ).toBeInTheDocument();
    });

    it("surfaces the backend error detail when loading fails", async () => {
      mockedGetModels.mockRejectedValue({
        response: {
          status: 404,
          data: { detail: "Project with ID 1 was not found." },
        },
      });

      render(<ModelsPage />);

      expect(
        await screen.findByText("Project with ID 1 was not found."),
      ).toBeInTheDocument();
    });
  });

  describe("registering a model version", () => {
    it("submits the form and prepends the new version", async () => {
      mockedGetModels.mockResolvedValue({
        total: 1,
        models: [makeModel({ id: 1, name: "Existing Classifier" })],
      });

      mockedRegisterModel.mockResolvedValue(
        makeModel({ id: 2, name: "Fraud Classifier", version: "2.0.0" }),
      );

      render(<ModelsPage />);

      await screen.findByText("Existing Classifier");

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /register model/i }));

      await waitFor(() => {
        expect(mockedRegisterModel).toHaveBeenCalledTimes(1);
      });

      expect(mockedRegisterModel).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          name: "Fraud Classifier",
          algorithm: "XGBoost",
          version: "1.0.0",
          framework: "scikit-learn",
          status: "registered",
        }),
      );

      const rows = screen.getAllByRole("row");

      expect(within(rows[1]).getByText("Fraud Classifier")).toBeInTheDocument();
    });

    it("sends edited metrics as numbers", async () => {
      mockedRegisterModel.mockResolvedValue(makeModel({ id: 2 }));

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      const accuracyField = screen.getByLabelText("ACCURACY");

      await user.clear(accuracyField);
      await user.type(accuracyField, "0.94");

      await user.click(screen.getByRole("button", { name: /register model/i }));

      await waitFor(() => {
        expect(mockedRegisterModel).toHaveBeenCalledWith(
          1,
          expect.objectContaining({
            metrics: expect.objectContaining({ accuracy: 0.94 }),
          }),
        );
      });
    });

    it("converts a blank artifact URI to null", async () => {
      mockedRegisterModel.mockResolvedValue(makeModel({ id: 2 }));

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      const artifactField = screen.getByLabelText(/artifact uri/i);

      await user.type(artifactField, "a");
      await user.clear(artifactField);

      await user.click(screen.getByRole("button", { name: /register model/i }));

      await waitFor(() => {
        expect(mockedRegisterModel).toHaveBeenCalledWith(
          1,
          expect.objectContaining({ artifact_uri: null }),
        );
      });
    });

    it("confirms a successful registration", async () => {
      mockedRegisterModel.mockResolvedValue(makeModel({ id: 2 }));

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /register model/i }));

      expect(
        await screen.findByText("Model version registered successfully."),
      ).toBeInTheDocument();
    });

    it("surfaces the API error detail when registration fails", async () => {
      mockedRegisterModel.mockRejectedValue({
        response: { data: { detail: "Model '1.0.0' already exists." } },
      });

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /register model/i }));

      expect(
        await screen.findByText("Model '1.0.0' already exists."),
      ).toBeInTheDocument();
    });

    it("renders FastAPI validation errors instead of crashing", async () => {
      mockedRegisterModel.mockRejectedValue({
        response: {
          status: 422,
          data: {
            detail: [
              {
                loc: ["body", "name"],
                msg: "String should have at most 150 characters",
                type: "string_too_long",
              },
            ],
          },
        },
      });

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /register model/i }));

      expect(
        await screen.findByText("String should have at most 150 characters"),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /model registry/i }),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedRegisterModel.mockRejectedValue(new Error("boom"));

      render(<ModelsPage />);

      const user = await fillRequiredFields();

      await user.click(screen.getByRole("button", { name: /register model/i }));

      expect(
        await screen.findByText("The model version could not be registered."),
      ).toBeInTheDocument();
    });
  });
});
