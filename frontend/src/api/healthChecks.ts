import { api } from "./client";

export type HealthCheck = {
  id: number;
  project_id: number;
  model_version_id: number;
  baseline_dataset_id: number;
  prediction_batch_id: number;
  status: string;
  health_score: number;
  metrics: Record<string, any>;
  drift: Record<string, any>;
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