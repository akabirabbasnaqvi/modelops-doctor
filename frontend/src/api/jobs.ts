import { api } from "./client";

export type AutomationJob = {
  id: number;
  project_id: number | null;
  job_type: string;
  status: string;
  celery_task_id: string | null;
  payload: Record<string, any>;
  result: Record<string, any>;
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