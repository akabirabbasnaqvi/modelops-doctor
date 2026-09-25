import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PredictionBatchesPage from "../PredictionBatchesPage";
import {
  getPredictionBatches,
  uploadPredictionBatch,
} from "../../api/predictions";
import type { PredictionBatch } from "../../api/predictions";

vi.mock("../../api/predictions", () => ({
  getPredictionBatches: vi.fn(),
  uploadPredictionBatch: vi.fn(),
}));

const mockedGetBatches = vi.mocked(getPredictionBatches);
const mockedUploadBatch = vi.mocked(uploadPredictionBatch);

function makeBatch(overrides: Partial<PredictionBatch> = {}): PredictionBatch {
  return {
    id: 4,
    project_id: 1,
    model_version_id: 2,
    file_name: "churn_predictions_v1.csv",
    file_path: "storage/prediction_logs/1/model_2_abc.csv",
    content_hash: "c".repeat(64),
    row_count: 500,
    is_labeled: true,
    status: "processed",
    error_message: null,
    uploaded_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function csvFile(name = "predictions.csv") {
  return new File(["predicted_label\n1\n"], name, { type: "text/csv" });
}

/**
 * The prediction CSV input is `required`, so jsdom's constraint validation
 * blocks both a click on the submit button and form.requestSubmit() while it
 * is empty — neither dispatches `submit`, leaving the component's own guard
 * unreachable. Dispatching submit directly exercises handleUpload instead of
 * the browser's validation.
 */
function submitForm() {
  const form = screen
    .getByRole("button", { name: /upload prediction log/i })
    .closest("form") as HTMLFormElement;

  fireEvent.submit(form);
}

function attachFile(file = csvFile()) {
  fireEvent.change(screen.getByLabelText(/prediction csv/i), {
    target: { files: [file] },
  });
}

describe("PredictionBatchesPage", () => {
  beforeEach(() => {
    mockedGetBatches.mockResolvedValue({ total: 0, batches: [] });
    mockedUploadBatch.mockReset();
  });

  describe("listing batches", () => {
    it("requests batches for the active project", async () => {
      render(<PredictionBatchesPage />);

      await waitFor(() => {
        expect(mockedGetBatches).toHaveBeenCalledWith(1);
      });
    });

    it("renders a batch as a table row", async () => {
      mockedGetBatches.mockResolvedValue({
        total: 1,
        batches: [makeBatch()],
      });

      render(<PredictionBatchesPage />);

      const row = (await screen.findByText("churn_predictions_v1.csv")).closest(
        "tr",
      ) as HTMLElement;

      expect(within(row).getByText("500")).toBeInTheDocument();
      expect(within(row).getByText("Yes")).toBeInTheDocument();
      expect(within(row).getByText("processed")).toBeInTheDocument();
    });

    it("reports No for an unlabeled batch", async () => {
      mockedGetBatches.mockResolvedValue({
        total: 1,
        batches: [makeBatch({ is_labeled: false })],
      });

      render(<PredictionBatchesPage />);

      expect(await screen.findByText("No")).toBeInTheDocument();
    });

    it("shows an error when batches cannot be loaded", async () => {
      mockedGetBatches.mockRejectedValue(new Error("network down"));

      render(<PredictionBatchesPage />);

      expect(
        await screen.findByText("Prediction batches could not be loaded."),
      ).toBeInTheDocument();
    });
  });

  describe("uploading a prediction log", () => {
    it("refuses to submit without a file", async () => {
      render(<PredictionBatchesPage />);

      submitForm();

      expect(
        await screen.findByText("Select a prediction CSV."),
      ).toBeInTheDocument();
      expect(mockedUploadBatch).not.toHaveBeenCalled();
    });

    it("uploads the file against the default model version", async () => {
      mockedUploadBatch.mockResolvedValue({ id: 4 });

      render(<PredictionBatchesPage />);

      attachFile();
      submitForm();

      await waitFor(() => {
        expect(mockedUploadBatch).toHaveBeenCalledWith(1, 1, expect.any(File));
      });
    });

    it("uploads against the chosen model version", async () => {
      mockedUploadBatch.mockResolvedValue({ id: 4 });

      render(<PredictionBatchesPage />);

      fireEvent.change(screen.getByLabelText(/model version id/i), {
        target: { value: "7" },
      });

      attachFile();
      submitForm();

      await waitFor(() => {
        expect(mockedUploadBatch).toHaveBeenCalledWith(1, 7, expect.any(File));
      });
    });

    it("confirms a successful upload and reloads the list", async () => {
      mockedUploadBatch.mockResolvedValue({ id: 4 });

      render(<PredictionBatchesPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText("Prediction log processed successfully."),
      ).toBeInTheDocument();

      expect(mockedGetBatches).toHaveBeenCalledTimes(2);
    });

    it("surfaces the API error detail when upload fails", async () => {
      mockedUploadBatch.mockRejectedValue({
        response: {
          data: {
            detail:
              "This prediction file has already been uploaded for the selected model version.",
          },
        },
      });

      render(<PredictionBatchesPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText(
          "This prediction file has already been uploaded for the selected model version.",
        ),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedUploadBatch.mockRejectedValue(new Error("boom"));

      render(<PredictionBatchesPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText("Prediction-log upload failed."),
      ).toBeInTheDocument();
    });
  });
});
