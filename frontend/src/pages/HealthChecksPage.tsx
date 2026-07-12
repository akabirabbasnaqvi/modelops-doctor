import { useEffect, useState } from "react";

import {
  getDiagnosisReport,
  getLatestHealthCheck,
  runHealthCheck,
} from "../api/healthChecks";

import type {
  DiagnosisReport,
  HealthCheck,
} from "../api/healthChecks";

const PROJECT_ID = 1;

export default function HealthChecksPage() {
  const [healthCheck, setHealthCheck] =
    useState<HealthCheck | null>(null);
  const [report, setReport] =
    useState<DiagnosisReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadLatestHealth() {
    try {
      const latest = await getLatestHealthCheck(PROJECT_ID);
      const diagnosis = await getDiagnosisReport(latest.id);

      setHealthCheck(latest);
      setReport(diagnosis);
    } catch {
      setError("No health check could be loaded.");
    }
  }

  useEffect(() => {
    void loadLatestHealth();
  }, []);

  async function handleRunHealthCheck() {
    try {
      setRunning(true);
      setError(null);

      const result = await runHealthCheck(
        PROJECT_ID,
        1,
        1,
        1
      );

      setHealthCheck(result.health_check);
      setReport(result.diagnosis_report);
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ??
          "The health check failed."
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <header className="page-header action-header">
        <div>
          <h1>Model Health</h1>
          <p>
            Review performance, drift, risk, and suggested actions.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={handleRunHealthCheck}
          disabled={running}
        >
          {running ? "Running..." : "Run Health Check"}
        </button>
      </header>

      {error && <div className="alert error">{error}</div>}

      {healthCheck && (
        <>
          <div className="metric-grid">
            <MetricCard
              title="Health Score"
              value={healthCheck.health_score.toFixed(2)}
            />

            <MetricCard
              title="Accuracy"
              value={
                healthCheck.metrics.accuracy?.toFixed(3) ??
                "N/A"
              }
            />

            <MetricCard
              title="F1 Score"
              value={
                healthCheck.metrics.f1?.toFixed(3) ?? "N/A"
              }
            />

            <MetricCard
              title="Drift Rate"
              value={`${(
                (healthCheck.drift.drift_rate ?? 0) * 100
              ).toFixed(0)}%`}
            />

            <MetricCard
              title="Average Confidence"
              value={
                healthCheck.metrics.average_confidence?.toFixed(
                  3
                ) ?? "N/A"
              }
            />
          </div>

          <section className="panel">
            <h2>Component Scores</h2>

            {Object.entries(
              healthCheck.component_scores
            ).map(([name, score]) => (
              <div className="score-row" key={name}>
                <span>{formatLabel(name)}</span>

                <div className="score-track">
                  <div
                    className="score-fill"
                    style={{
                      width: `${score}%`,
                    }}
                  />
                </div>

                <strong>{score.toFixed(1)}</strong>
              </div>
            ))}
          </section>
        </>
      )}

      {report && (
        <section className="panel">
          <h2>Diagnosis Report</h2>

          <p>{report.summary}</p>

          <p>
            <strong>Risk:</strong>{" "}
            <span className={`status-badge ${report.risk_level}`}>
              {report.risk_level}
            </span>
          </p>

          <p>
            <strong>Retraining recommended:</strong>{" "}
            {report.retraining_recommended ? "Yes" : "No"}
          </p>

          <h3>Findings</h3>

          <ul>
            {report.findings.map((finding) => (
              <li key={finding.code}>
                <strong>{finding.code}:</strong>{" "}
                {finding.message}
              </li>
            ))}
          </ul>

          <h3>Recommendations</h3>

          <ol>
            {report.recommendations.map(
              (recommendation) => (
                <li key={recommendation}>
                  {recommendation}
                </li>
              )
            )}
          </ol>
        </section>
      )}
    </div>
  );
}

function MetricCard({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <article className="metric-card">
      <span>{title}</span>
      <strong>{value}</strong>
    </article>
  );
}

function formatLabel(value: string) {
  return value
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}