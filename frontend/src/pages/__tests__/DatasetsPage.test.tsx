import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DatasetsPage from "../DatasetsPage";
import { getDatasets, uploadDataset } from "../../api/datasets";
import type { Dataset } from "../../api/datasets";

vi.mock("../../api/datasets", () => ({
  getDatasets: vi.fn(),
  uploadDataset: vi.fn(),
}));

const mockedGetDatasets = vi.mocked(getDatasets);
const mockedUploadDataset = vi.mocked(uploadDataset);

function makeDataset(overrides: Partial<Dataset> = {}): Dataset {
  return {
    id: 3,
    project_id: 1,
    dataset_type: "training",
    version: "1.0.0",
    file_name: "churn_training.csv",
    file_path: "storage/datasets/1/training_1.0.0_abc.csv",
    content_hash: "a".repeat(64),
    schema_hash: "b".repeat(64),
    row_count: 1200,
    column_count: 9,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function csvFile(name = "churn.csv") {
  return new File(["age,churn\n31,1\n"], name, { type: "text/csv" });
}

/**
 * The CSV input is `required`, so jsdom's constraint validation blocks both
 * a click on the submit button and form.requestSubmit() while it is empty.
 * Neither ever dispatches `submit`, so the component's own guard is
 * unreachable through them. Dispatching submit directly is what lets these
 * tests exercise handleUpload rather than the browser's validation.
 */
function submitForm() {
  const form = screen
    .getByRole("button", { name: /upload and profile/i })
    .closest("form") as HTMLFormElement;

  fireEvent.submit(form);
}

function attachFile(file = csvFile()) {
  fireEvent.change(screen.getByLabelText(/csv file/i), {
    target: { files: [file] },
  });
}

describe("DatasetsPage", () => {
  beforeEach(() => {
    mockedGetDatasets.mockResolvedValue({ total: 0, datasets: [] });
    mockedUploadDataset.mockReset();
  });

  describe("listing datasets", () => {
    it("requests datasets for the active project", async () => {
      render(<DatasetsPage />);

      await waitFor(() => {
        expect(mockedGetDatasets).toHaveBeenCalledWith(1);
      });
    });

    it("renders a dataset as a table row", async () => {
      mockedGetDatasets.mockResolvedValue({
        total: 1,
        datasets: [makeDataset()],
      });

      render(<DatasetsPage />);

      const row = (await screen.findByText("churn_training.csv")).closest(
        "tr",
      ) as HTMLElement;

      expect(within(row).getByText("training")).toBeInTheDocument();
      expect(within(row).getByText("1.0.0")).toBeInTheDocument();
      expect(within(row).getByText("1200")).toBeInTheDocument();
      expect(within(row).getByText("9")).toBeInTheDocument();
    });

    it("shows an error when datasets cannot be loaded", async () => {
      mockedGetDatasets.mockRejectedValue(new Error("network down"));

      render(<DatasetsPage />);

      expect(
        await screen.findByText("Datasets could not be loaded."),
      ).toBeInTheDocument();
    });
  });

  describe("uploading a dataset", () => {
    it("refuses to submit without a file", async () => {
      render(<DatasetsPage />);

      submitForm();

      expect(await screen.findByText("Select a CSV file.")).toBeInTheDocument();
      expect(mockedUploadDataset).not.toHaveBeenCalled();
    });

    it("uploads the selected file with the default type and version", async () => {
      mockedUploadDataset.mockResolvedValue({ id: 3 });

      render(<DatasetsPage />);

      attachFile();
      submitForm();

      await waitFor(() => {
        expect(mockedUploadDataset).toHaveBeenCalledWith(
          1,
          "training",
          "2.0.0",
          expect.any(File),
        );
      });
    });

    it("sends the chosen dataset type and version", async () => {
      mockedUploadDataset.mockResolvedValue({ id: 3 });

      render(<DatasetsPage />);

      fireEvent.change(screen.getByLabelText(/dataset type/i), {
        target: { value: "production" },
      });

      fireEvent.change(screen.getByLabelText(/version/i), {
        target: { value: "3.1.0" },
      });

      attachFile();
      submitForm();

      await waitFor(() => {
        expect(mockedUploadDataset).toHaveBeenCalledWith(
          1,
          "production",
          "3.1.0",
          expect.any(File),
        );
      });
    });

    it("confirms a successful upload and reloads the list", async () => {
      mockedUploadDataset.mockResolvedValue({ id: 3 });

      render(<DatasetsPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText("Dataset uploaded and profiled successfully."),
      ).toBeInTheDocument();

      expect(mockedGetDatasets).toHaveBeenCalledTimes(2);
    });

    it("surfaces the API error detail when upload fails", async () => {
      mockedUploadDataset.mockRejectedValue({
        response: {
          data: { detail: "Target column 'churn' was not found in the CSV." },
        },
      });

      render(<DatasetsPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText(
          "Target column 'churn' was not found in the CSV.",
        ),
      ).toBeInTheDocument();
    });

    it("falls back to a generic message when the error has no detail", async () => {
      mockedUploadDataset.mockRejectedValue(new Error("boom"));

      render(<DatasetsPage />);

      attachFile();
      submitForm();

      expect(
        await screen.findByText("Dataset upload failed."),
      ).toBeInTheDocument();
    });
  });
});
