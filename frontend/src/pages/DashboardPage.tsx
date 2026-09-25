import { useEffect, useState } from "react";

import { getDashboard } from "../api/dashboard";
import DriftChart from "../components/DriftChart";
import HealthGauge from "../components/HealthGauge";
import RecentJobsTable from "../components/RecentJobsTable";
import StatCard from "../components/StatCard";

type DashboardData = {
  project_id: number;
  project_name: string;
  counts: {
    models: number;
    datasets: number;
    prediction_batches: number;
    health_checks: number;
  };
  latest_health: {
    health_check_id: number;
    health_score: number;
    status: string;
    risk_level: string | null;
    retraining_recommended: boolean | null;
    drifted_features: string[];
    recommendations: string[];
  } | null;
  recent_jobs: Array<{
    id: number;
    job_type: string;
    status: string;
    created_at: string;
    finished_at: string | null;
  }>;
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard(1)
      .then((dashboardData) => {
        setData(dashboardData);
      })
      .catch(() => {
        setError(
          "The dashboard could not be loaded. Confirm that the FastAPI backend is running."
        );
      });
  }, []);

  if (error) {
    return (
      <div>
        <h1>Dashboard unavailable</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!data) {
    return <h2>Loading dashboard...</h2>;
  }

  const latestHealth = data.latest_health;

  return (
    <div>
      <header className="page-header">
        <h1>{data.project_name}</h1>

        <p>
          Monitor registered models, datasets, prediction batches,
          automated jobs, and model health.
        </p>
      </header>

      <div className="dashboard-grid">
        <StatCard title="Models" value={data.counts.models} />

        <StatCard title="Datasets" value={data.counts.datasets} />

        <StatCard
          title="Prediction Batches"
          value={data.counts.prediction_batches}
        />

        <StatCard
          title="Health Checks"
          value={data.counts.health_checks}
        />
      </div>

      <div className="panel health-summary">
        <HealthGauge score={latestHealth?.health_score ?? 0} />

        <div>
          <h3>Status</h3>
          <p>{latestHealth?.status ?? "No health check available"}</p>

          <h3>Risk Level</h3>
          <p>{latestHealth?.risk_level ?? "Not available"}</p>

          <h3>Retraining Recommended</h3>
          <p>
            {latestHealth?.retraining_recommended === null ||
            latestHealth?.retraining_recommended === undefined
              ? "Not available"
              : latestHealth.retraining_recommended
                ? "Yes"
                : "No"}
          </p>
        </div>
      </div>

      <section className="panel">
        <h2>Recent Jobs</h2>

        <div className="table-wrapper">
          <RecentJobsTable jobs={data.recent_jobs} />
        </div>
      </section>

      <section className="panel">
        <h2>Drifted Features</h2>

        <p>
          Features whose current distributions differ from the
          training dataset.
        </p>

        <DriftChart
          driftedFeatures={
            latestHealth?.drifted_features ?? []
          }
        />
      </section>
    </div>
  );
}