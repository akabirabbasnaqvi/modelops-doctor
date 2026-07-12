import { api } from "./client";

import type {
  Project,
  ProjectCreateRequest,
  ProjectListResponse,
} from "../types/project";

export async function getProjects(): Promise<ProjectListResponse> {
  const response = await api.get<ProjectListResponse>("/projects");

  return response.data;
}

export async function getProject(
  projectId: number
): Promise<Project> {
  const response = await api.get<Project>(
    `/projects/${projectId}`
  );

  return response.data;
}

export async function createProject(
  projectData: ProjectCreateRequest
): Promise<Project> {
  const response = await api.post<Project>(
    "/projects",
    projectData
  );

  return response.data;
}