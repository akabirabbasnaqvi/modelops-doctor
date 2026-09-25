/**
 * Contract tests for the typed HTTP clients.
 *
 * The page suites mock this layer, so without these the request paths are
 * never executed and a renamed backend route would break the app with every
 * test still green. These pin the method, URL and payload of each call
 * against the FastAPI routes in backend/app/api/routes/.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../client";
import { getDashboard } from "../dashboard";
import { getDatasetProfile, getDatasets, uploadDataset } from "../datasets";
import {
  getDiagnosisReport,
  getLatestHealthCheck,
  runHealthCheck,
} from "../healthChecks";
import { getJobs, queueHealthCheck } from "../jobs";
import { getModels, registerModel } from "../models";
import { getPredictionBatches, uploadPredictionBatch } from "../predictions";
import { createProject, getProject, getProjects } from "../projects";

vi.mock("../client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockedGet = vi.mocked(api.get);
const mockedPost = vi.mocked(api.post);

function csvFile() {
  return new File(["a,b\n1,2\n"], "data.csv", { type: "text/csv" });
}

describe("API clients", () => {
  beforeEach(() => {
    mockedGet.mockReset().mockResolvedValue({ data: { ok: true } });
    mockedPost.mockReset().mockResolvedValue({ data: { ok: true } });
  });

  describe("projects", () => {
    it("lists projects", async () => {
      await expect(getProjects()).resolves.toEqual({ ok: true });
      expect(mockedGet).toHaveBeenCalledWith("/projects");
    });

    it("fetches one project by id", async () => {
      await getProject(7);

      expect(mockedGet).toHaveBeenCalledWith("/projects/7");
    });

    it("creates a project", async () => {
      const payload = {
        name: "Fraud Monitoring",
        description: null,
        problem_type: "binary_classification" as const,
        target_column: "is_fraud",
        positive_class: null,
        metric_priority: "f1",
        owner: null,
      };

      await createProject(payload);

      expect(mockedPost).toHaveBeenCalledWith("/projects", payload);
    });
  });

  describe("model versions", () => {
    it("lists models for a project", async () => {
      await getModels(3);

      expect(mockedGet).toHaveBeenCalledWith("/projects/3/models");
    });

    it("registers a model version", async () => {
      const payload = {
        name: "Churn Classifier",
        version: "1.0.0",
        algorithm: "Random Forest",
        framework: "scikit-learn",
        metrics: { f1: 0.83 },
        artifact_uri: null,
        status: "registered",
        training_date: null,
      };

      await registerModel(3, payload);

      expect(mockedPost).toHaveBeenCalledWith("/projects/3/models", payload);
    });
  });

  describe("datasets", () => {
    it("lists datasets for a project", async () => {
      await getDatasets(3);

      expect(mockedGet).toHaveBeenCalledWith("/projects/3/datasets");
    });

    it("fetches a dataset profile", async () => {
      await getDatasetProfile(11);

      expect(mockedGet).toHaveBeenCalledWith("/datasets/11/profile");
    });

    it("uploads a dataset as multipart form data", async () => {
      await uploadDataset(3, "training", "1.0.0", csvFile());

      const [url, body] = mockedPost.mock.calls[0];

      expect(url).toBe("/projects/3/datasets");
      expect(body).toBeInstanceOf(FormData);

      const formData = body as FormData;

      expect(formData.get("dataset_type")).toBe("training");
      expect(formData.get("version")).toBe("1.0.0");
      expect(formData.get("file")).toBeInstanceOf(File);
    });
  });

  describe("prediction batches", () => {
    it("lists prediction batches for a project", async () => {
      await getPredictionBatches(3);

      expect(mockedGet).toHaveBeenCalledWith("/projects/3/prediction-batches");
    });

    it("uploads a prediction log as multipart form data", async () => {
      await uploadPredictionBatch(3, 5, csvFile());

      const [url, body] = mockedPost.mock.calls[0];

      expect(url).toBe("/projects/3/prediction-batches");

      const formData = body as FormData;

      expect(formData.get("model_version_id")).toBe("5");
      expect(formData.get("file")).toBeInstanceOf(File);
    });
  });

  describe("health checks", () => {
    it("runs a health check with the pipeline ids in the body", async () => {
      await runHealthCheck(1, 2, 3, 4);

      expect(mockedPost).toHaveBeenCalledWith("/projects/1/health-checks/run", {
        model_version_id: 2,
        baseline_dataset_id: 3,
        prediction_batch_id: 4,
      });
    });

    it("fetches the latest health check", async () => {
      await getLatestHealthCheck(1);

      expect(mockedGet).toHaveBeenCalledWith(
        "/projects/1/health-checks/latest",
      );
    });

    it("fetches a diagnosis report", async () => {
      await getDiagnosisReport(11);

      expect(mockedGet).toHaveBeenCalledWith("/health-checks/11/report");
    });
  });

  describe("automation jobs", () => {
    it("lists jobs", async () => {
      await getJobs();

      expect(mockedGet).toHaveBeenCalledWith("/jobs");
    });

    it("queues a background health check", async () => {
      await queueHealthCheck(1);

      expect(mockedPost).toHaveBeenCalledWith(
        "/projects/1/health-checks/background",
        {
          model_version_id: 1,
          baseline_dataset_id: 1,
          prediction_batch_id: 1,
        },
      );
    });
  });

  describe("dashboard", () => {
    it("fetches the dashboard for a project", async () => {
      await getDashboard(1);

      expect(mockedGet).toHaveBeenCalledWith("/projects/1/dashboard");
    });
  });
});
