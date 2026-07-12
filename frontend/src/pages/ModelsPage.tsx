import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getModels,
  registerModel,
} from "../api/models";

import type {
  ModelVersion,
  ModelVersionCreateRequest,
} from "../api/models";

const PROJECT_ID = 1;

const initialForm: ModelVersionCreateRequest = {
  name: "",
  version: "1.0.0",
  algorithm: "",
  framework: "scikit-learn",
  metrics: {
    accuracy: 0,
    precision: 0,
    recall: 0,
    f1: 0,
  },
  artifact_uri: null,
  status: "registered",
  training_date: null,
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [formData, setFormData] =
    useState<ModelVersionCreateRequest>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadModels() {
    try {
      setLoading(true);
      setError(null);

      const response = await getModels(PROJECT_ID);

      setModels(response.models);
    } catch {
      setError("Model versions could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadModels();
  }, []);

  function updateMetric(
    metric: string,
    value: string
  ) {
    setFormData((current) => ({
      ...current,
      metrics: {
        ...current.metrics,
        [metric]: Number(value),
      },
    }));
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    try {
      setError(null);
      setSuccess(null);

      const createdModel = await registerModel(
        PROJECT_ID,
        formData
      );

      setModels((current) => [
        createdModel,
        ...current,
      ]);

      setFormData(initialForm);
      setSuccess("Model version registered successfully.");
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ??
          "The model version could not be registered."
      );
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>Model Registry</h1>
        <p>
          Register, compare, and monitor machine-learning
          model versions.
        </p>
      </header>

      {error && <div className="alert error">{error}</div>}
      {success && (
        <div className="alert success">{success}</div>
      )}

      <section className="panel">
        <h2>Register Model Version</h2>

        <form
          className="form-grid"
          onSubmit={handleSubmit}
        >
          <label>
            Model Name
            <input
              required
              value={formData.name}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  name: event.target.value,
                })
              }
            />
          </label>

          <label>
            Version
            <input
              required
              value={formData.version}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  version: event.target.value,
                })
              }
            />
          </label>

          <label>
            Algorithm
            <input
              required
              value={formData.algorithm}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  algorithm: event.target.value,
                })
              }
            />
          </label>

          <label>
            Framework
            <input
              required
              value={formData.framework}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  framework: event.target.value,
                })
              }
            />
          </label>

          {["accuracy", "precision", "recall", "f1"].map(
            (metric) => (
              <label key={metric}>
                {metric.toUpperCase()}
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={formData.metrics[metric] ?? 0}
                  onChange={(event) =>
                    updateMetric(metric, event.target.value)
                  }
                />
              </label>
            )
          )}

          <label className="full-width">
            Artifact URI
            <input
              value={formData.artifact_uri ?? ""}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  artifact_uri:
                    event.target.value || null,
                })
              }
              placeholder="artifacts/model.joblib"
            />
          </label>

          <button className="primary-button" type="submit">
            Register Model
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Registered Versions</h2>

        {loading ? (
          <p>Loading models...</p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Version</th>
                  <th>Algorithm</th>
                  <th>Framework</th>
                  <th>F1</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {models.map((model) => (
                  <tr key={model.id}>
                    <td>{model.id}</td>
                    <td>{model.name}</td>
                    <td>{model.version}</td>
                    <td>{model.algorithm}</td>
                    <td>{model.framework}</td>
                    <td>
                      {model.metrics.f1?.toFixed(3) ?? "N/A"}
                    </td>
                    <td>
                      <span className="status-badge completed">
                        {model.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
