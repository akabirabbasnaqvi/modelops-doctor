import { api } from "./client";

/**
 * Result recorded by the health-check Celery task in
 * app/workers/tasks.py. Empty while a job is queued or running, and empty
 * on failure, so every field is optional.
 */
export type AutomationJobResult = {
  health_check_id?: number;
  diagnosis_report_id?: number;
  health_score?: number | null;
  status?: string;
  risk_level?: string;
  retraining_recommended?: boolean;
};

export type AutomationJob = {
  id: number;
  project_id: number | null;
  job_type: string;
  status: string;
  celery_task_id: string | null;
  payload: Record<string, unknown>;
  result: AutomationJobResult;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export async function getJobs() {
  const response = await api.get<{
    total: number;
    jobs: AutomationJob[];
  }>("/jobs");

  return response.data;
}

export async function queueHealthCheck(
  projectId: number
) {
  const response = await api.post(
    `/projects/${projectId}/health-checks/background`,
    {
      model_version_id: 1,
      baseline_dataset_id: 1,
      prediction_batch_id: 1,
    }
  );

  return response.data;
}