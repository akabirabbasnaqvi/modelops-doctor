import { useEffect, useState } from "react";

import {
  getJobs,
  queueHealthCheck,
} from "../api/jobs";

import type { AutomationJob } from "../api/jobs";

const PROJECT_ID = 1;

export default function JobsPage() {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);
  const [queuing, setQueuing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadJobs() {
    try {
      const response = await getJobs();
      setJobs(response.jobs);
    } catch {
      setError("Automation jobs could not be loaded.");
    }
  }

  useEffect(() => {
    void loadJobs();

    const interval = window.setInterval(() => {
      void loadJobs();
    }, 5000);

    return () => window.clearInterval(interval);
  }, []);

  async function handleQueueJob() {
    try {
      setQueuing(true);
      setError(null);

      await queueHealthCheck(PROJECT_ID);
      await loadJobs();
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ??
          "The background task could not be queued."
      );
    } finally {
      setQueuing(false);
    }
  }

  return (
    <div>
      <header className="page-header action-header">
        <div>
          <h1>Automation Jobs</h1>
          <p>
            Monitor queued and completed Celery background tasks.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={handleQueueJob}
          disabled={queuing}
        >
          {queuing
            ? "Queuing..."
            : "Queue Health Check"}
        </button>
      </header>

      {error && <div className="alert error">{error}</div>}

      <section className="panel">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Health Score</th>
                <th>Error</th>
                <th>Created</th>
              </tr>
            </thead>

            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.job_type}</td>
                  <td>
                    <span
                      className={`status-badge ${job.status}`}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td>
                    {job.result.health_score ?? "N/A"}
                  </td>
                  <td>{job.error_message ?? "—"}</td>
                  <td>
                    {new Date(
                      job.created_at
                    ).toLocaleString()}
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