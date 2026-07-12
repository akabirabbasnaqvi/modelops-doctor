import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getPredictionBatches,
  uploadPredictionBatch,
} from "../api/predictions";

import type { PredictionBatch } from "../api/predictions";

const PROJECT_ID = 1;

export default function PredictionBatchesPage() {
  const [batches, setBatches] =
    useState<PredictionBatch[]>([]);
  const [modelVersionId, setModelVersionId] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadBatches() {
    try {
      const response = await getPredictionBatches(
        PROJECT_ID
      );

      setBatches(response.batches);
    } catch {
      setError("Prediction batches could not be loaded.");
    }
  }

  useEffect(() => {
    void loadBatches();
  }, []);

  async function handleUpload(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!file) {
      setError("Select a prediction CSV.");
      return;
    }

    try {
      setError(null);
      setMessage(null);

      await uploadPredictionBatch(
        PROJECT_ID,
        modelVersionId,
        file
      );

      setMessage("Prediction log processed successfully.");
      setFile(null);
      await loadBatches();
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ??
          "Prediction-log upload failed."
      );
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>Prediction Logs</h1>
        <p>
          Upload labeled or unlabeled production predictions.
        </p>
      </header>

      {error && <div className="alert error">{error}</div>}
      {message && (
        <div className="alert success">{message}</div>
      )}

      <section className="panel">
        <h2>Upload Prediction Batch</h2>

        <form
          className="form-grid"
          onSubmit={handleUpload}
        >
          <label>
            Model Version ID
            <input
              type="number"
              min="1"
              value={modelVersionId}
              onChange={(event) =>
                setModelVersionId(
                  Number(event.target.value)
                )
              }
            />
          </label>

          <label className="full-width">
            Prediction CSV
            <input
              required
              type="file"
              accept=".csv,text/csv"
              onChange={(event) =>
                setFile(event.target.files?.[0] ?? null)
              }
            />
          </label>

          <button className="primary-button" type="submit">
            Upload Prediction Log
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Prediction Batches</h2>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Model</th>
                <th>File</th>
                <th>Rows</th>
                <th>Labeled</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {batches.map((batch) => (
                <tr key={batch.id}>
                  <td>{batch.id}</td>
                  <td>{batch.model_version_id}</td>
                  <td>{batch.file_name}</td>
                  <td>{batch.row_count}</td>
                  <td>{batch.is_labeled ? "Yes" : "No"}</td>
                  <td>
                    <span
                      className={`status-badge ${batch.status}`}
                    >
                      {batch.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
