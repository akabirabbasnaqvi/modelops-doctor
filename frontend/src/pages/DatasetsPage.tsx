import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getDatasets,
  uploadDataset,
} from "../api/datasets";

import type { Dataset } from "../api/datasets";

const PROJECT_ID = 1;

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetType, setDatasetType] =
    useState("training");
  const [version, setVersion] = useState("2.0.0");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] =
    useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function loadDatasets() {
    try {
      const result = await getDatasets(PROJECT_ID);
      setDatasets(result.datasets);
    } catch {
      setError("Datasets could not be loaded.");
    }
  }

  useEffect(() => {
    void loadDatasets();
  }, []);

  async function handleUpload(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!file) {
      setError("Select a CSV file.");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);

      await uploadDataset(
        PROJECT_ID,
        datasetType,
        version,
        file
      );

      setSuccess("Dataset uploaded and profiled successfully.");
      setFile(null);
      await loadDatasets();
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ??
          "Dataset upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>Datasets</h1>
        <p>
          Upload baseline, evaluation, and production datasets.
        </p>
      </header>

      {error && <div className="alert error">{error}</div>}
      {success && (
        <div className="alert success">{success}</div>
      )}

      <section className="panel">
        <h2>Upload CSV Dataset</h2>

        <form
          className="form-grid"
          onSubmit={handleUpload}
        >
          <label>
            Dataset Type
            <select
              value={datasetType}
              onChange={(event) =>
                setDatasetType(event.target.value)
              }
            >
              <option value="training">Training</option>
              <option value="validation">Validation</option>
              <option value="testing">Testing</option>
              <option value="production">Production</option>
            </select>
          </label>

          <label>
            Version
            <input
              required
              value={version}
              onChange={(event) =>
                setVersion(event.target.value)
              }
            />
          </label>

          <label className="full-width">
            CSV File
            <input
              required
              type="file"
              accept=".csv,text/csv"
              onChange={(event) =>
                setFile(event.target.files?.[0] ?? null)
              }
            />
          </label>

          <button
            className="primary-button"
            type="submit"
            disabled={uploading}
          >
            {uploading
              ? "Uploading..."
              : "Upload and Profile"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Registered Datasets</h2>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Version</th>
                <th>File</th>
                <th>Rows</th>
                <th>Columns</th>
              </tr>
            </thead>

            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.id}>
                  <td>{dataset.id}</td>
                  <td>{dataset.dataset_type}</td>
                  <td>{dataset.version}</td>
                  <td>{dataset.file_name}</td>
                  <td>{dataset.row_count}</td>
                  <td>{dataset.column_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
