import { api } from "./client";

export type Dataset = {
  id: number;
  project_id: number;
  dataset_type: string;
  version: string;
  file_name: string;
  file_path: string;
  content_hash: string;
  schema_hash: string;
  row_count: number;
  column_count: number;
  created_at: string;
};

export type DatasetListResponse = {
  total: number;
  datasets: Dataset[];
};

export async function getDatasets(
  projectId: number
): Promise<DatasetListResponse> {
  const response = await api.get<DatasetListResponse>(
    `/projects/${projectId}/datasets`
  );

  return response.data;
}

export async function uploadDataset(
  projectId: number,
  datasetType: string,
  version: string,
  file: File
) {
  const formData = new FormData();

  formData.append("dataset_type", datasetType);
  formData.append("version", version);
  formData.append("file", file);

  const response = await api.post(
    `/projects/${projectId}/datasets`,
    formData
  );

  return response.data;
}

export async function getDatasetProfile(
  datasetId: number
) {
  const response = await api.get(
    `/datasets/${datasetId}/profile`
  );

  return response.data;
}
