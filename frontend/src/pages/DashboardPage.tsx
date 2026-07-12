import { useEffect, useState } from "react";
import { getDashboard } from "../api/dashboard";

export default function DashboardPage() {
  const [data, setData] = useState<any>();

  useEffect(() => {
    getDashboard(1).then(setData);
  }, []);

  if (!data) {
    return <h2>Loading dashboard...</h2>;
  }

  return (
    <div>
      <h1>{data.project_name}</h1>

      <h2>
        Health Score:
        {data.latest_health?.health_score}
      </h2>

      <h3>Status:</h3>

      <p>{data.latest_health?.status}</p>

      <h3>Risk Level:</h3>

      <p>{data.latest_health?.risk_level}</p>

      <h3>Project Counts</h3>

      <ul>
        <li>
          Models: {data.counts.models}
        </li>

        <li>
          Datasets: {data.counts.datasets}
        </li>

        <li>
          Prediction Batches:
          {data.counts.prediction_batches}
        </li>

        <li>
          Health Checks:
          {data.counts.health_checks}
        </li>
      </ul>
    </div>
  );
}