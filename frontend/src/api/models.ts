import { api } from "./client";

export type ModelVersion = {
  id: number;
  project_id: number;
  name: string;
  version: string;
  algorithm: string;
  framework: string;
  metrics: Record<string, number>;
  artifact_uri: string | null;
  status: string;
  training_date: string | null;
  created_at: string;
  updated_at: string;
};

export type ModelVersionListResponse = {
  total: number;
  models: ModelVersion[];
};

export type ModelVersionCreateRequest = {
  name: string;
  version: string;
  algorithm: string;
  framework: string;
  metrics: Record<string, number>;
  artifact_uri: string | null;
  status: string;
  training_date: string | null;
};

export async function getModels(
  projectId: number
): Promise<ModelVersionListResponse> {
  const response = await api.get<ModelVersionListResponse>(
    `/projects/${projectId}/models`
  );

  return response.data;
}

export async function registerModel(
  projectId: number,
  modelData: ModelVersionCreateRequest
): Promise<ModelVersion> {
  const response = await api.post<ModelVersion>(
    `/projects/${projectId}/models`,
    modelData
  );

  return response.data;
}