export type ProblemType =
  | "binary_classification"
  | "multiclass_classification";

export type Project = {
  id: number;
  name: string;
  description: string | null;
  problem_type: string;
  target_column: string;
  positive_class: string | null;
  metric_priority: string;
  owner: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = {
  total: number;
  projects: Project[];
};

export type ProjectCreateRequest = {
  name: string;
  description: string | null;
  problem_type: ProblemType;
  target_column: string;
  positive_class: string | null;
  metric_priority: string;
  owner: string | null;
};