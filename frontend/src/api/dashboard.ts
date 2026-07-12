import { api } from "./client";

export async function getDashboard(projectId: number) {
  const response = await api.get(
    `/projects/${projectId}/dashboard`
  );

  return response.data;
}