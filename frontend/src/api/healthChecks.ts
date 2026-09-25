import { api } from "./client";

/**
 * Classification metrics produced by app/mlops/metrics.py.
 *
 * Confidence and roc_auc are null when the prediction log carries no
 * confidence column or the problem is not binary, so every numeric field is
 * optional and nullable. The index signature covers the remaining keys
 * (confusion_matrix, per_class, class distributions) that the UI does not
 * read yet.
 */
export type HealthCheckMetrics = {
  sample_count?: number;
  accuracy?: number | null;
  precision?: number | null;
  recall?: number | null;
  f1?: number | null;
  error_rate?: number | null;
  roc_auc?: number | null;
  average_confidence?: number | null;
  low_confidence_rate?: number | null;
  minimum_confidence?: number | null;
  maximum_confidence?: number | null;
  [key: string]: unknown;
};

/** Drift summary produced by app/mlops/drift.py. */
export type DriftSummary = {
  feature_count?: number;
  drifted_feature_count?: number;
  drift_rate?: number | null;
  drifted_features?: string[];
  [key: string]: unknown;
};

export type HealthCheck = {
  id: number;
  project_id: number;
  model_version_id: number;
  baseline_dataset_id: number;
  prediction_batch_id: number;
  status: string;
  health_score: number;
  metrics: HealthCheckMetrics;
  drift: DriftSummary;
  component_scores: Record<string, number>;
  missing_rate: number;
  created_at: string;
};

export type DiagnosisReport = {
  id: number;
  health_check_id: number;
  summary: string;
  risk_level: string;
  retraining_recommended: boolean;
  findings: Array<{
    code: string;
    severity: string;
    message: string;
  }>;
  recommendations: string[];
  created_at: string;
};

export async function runHealthCheck(
  projectId: number,
  modelVersionId: number,
  baselineDatasetId: number,
  predictionBatchId: number
) {
  const response = await api.post(
    `/projects/${projectId}/health-checks/run`,
    {
      model_version_id: modelVersionId,
      baseline_dataset_id: baselineDatasetId,
      prediction_batch_id: predictionBatchId,
    }
  );

  return response.data;
}

export async function getLatestHealthCheck(
  projectId: number
): Promise<HealthCheck> {
  const response = await api.get<HealthCheck>(
    `/projects/${projectId}/health-checks/latest`
  );

  return response.data;
}

export async function getDiagnosisReport(
  healthCheckId: number
): Promise<DiagnosisReport> {
  const response = await api.get<DiagnosisReport>(
    `/health-checks/${healthCheckId}/report`
  );

  return response.data;
}