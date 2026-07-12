import { api } from "./client";

export type PredictionBatch = {
  id: number;
  project_id: number;
  model_version_id: number;
  file_name: string;
  file_path: string;
  content_hash: string;
  row_count: number;
  is_labeled: boolean;
  status: string;
  error_message: string | null;
  uploaded_at: string;
};

export async function getPredictionBatches(
  projectId: number
) {
  const response = await api.get<{
    total: number;
    batches: PredictionBatch[];
  }>(`/projects/${projectId}/prediction-batches`);

  return response.data;
}

export async function uploadPredictionBatch(
  projectId: number,
  modelVersionId: number,
  file: File
) {
  const formData = new FormData();

  formData.append(
    "model_version_id",
    String(modelVersionId)
  );
  formData.append("file", file);

  const response = await api.post(
    `/projects/${projectId}/prediction-batches`,
    formData
  );

  return response.data;
}