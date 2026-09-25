import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

import { getErrorMessage } from "../api/errors";
import { useFormState } from "../hooks/useFormState";
import {
  createProject,
  getProjects,
} from "../api/projects";

import type {
  ProblemType,
  Project,
  ProjectCreateRequest,
} from "../types/project";

const initialFormData: ProjectCreateRequest = {
  name: "",
  description: "",
  problem_type: "binary_classification",
  target_column: "",
  positive_class: "1",
  metric_priority: "f1",
  owner: "",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const {
    values: formData,
    updateField,
    reset: resetForm,
  } = useFormState<ProjectCreateRequest>(initialFormData);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  async function loadProjects() {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getProjects();

      setProjects(response.projects);
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Projects could not be loaded. Confirm that the backend is running."
        )
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    try {
      setIsCreating(true);
      setError(null);
      setSuccessMessage(null);

      const normalizedData: ProjectCreateRequest = {
        ...formData,
        description: formData.description?.trim() || null,
        positive_class:
          formData.positive_class?.trim() || null,
        owner: formData.owner?.trim() || null,
      };

      const newProject = await createProject(normalizedData);

      setProjects((currentProjects) => [
        newProject,
        ...currentProjects,
      ]);

      resetForm();

      setSuccessMessage(
        `Project "${newProject.name}" was created successfully.`
      );
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "The project could not be created."
        )
      );
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>Projects</h1>

        <p>
          Create and manage machine-learning monitoring
          workspaces.
        </p>
      </header>

      {error && <div className="alert error">{error}</div>}

      {successMessage && (
        <div className="alert success">{successMessage}</div>
      )}

      <section className="panel">
        <h2>Create Project</h2>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Project Name
            <input
              required
              minLength={3}
              value={formData.name}
              onChange={(event) =>
                updateField("name", event.target.value)
              }
            />
          </label>

          <label>
            Problem Type
            <select
              value={formData.problem_type}
              onChange={(event) =>
                updateField(
                  "problem_type",
                  event.target.value as ProblemType
                )
              }
            >
              <option value="binary_classification">
                Binary Classification
              </option>

              <option value="multiclass_classification">
                Multiclass Classification
              </option>
            </select>
          </label>

          <label>
            Target Column
            <input
              required
              value={formData.target_column}
              onChange={(event) =>
                updateField(
                  "target_column",
                  event.target.value
                )
              }
            />
          </label>

          <label>
            Positive Class
            <input
              value={formData.positive_class ?? ""}
              onChange={(event) =>
                updateField(
                  "positive_class",
                  event.target.value
                )
              }
            />
          </label>

          <label>
            Priority Metric
            <select
              value={formData.metric_priority}
              onChange={(event) =>
                updateField(
                  "metric_priority",
                  event.target.value
                )
              }
            >
              <option value="f1">F1 Score</option>
              <option value="accuracy">Accuracy</option>
              <option value="precision">Precision</option>
              <option value="recall">Recall</option>
              <option value="roc_auc">ROC-AUC</option>
            </select>
          </label>

          <label>
            Owner
            <input
              value={formData.owner ?? ""}
              onChange={(event) =>
                updateField("owner", event.target.value)
              }
            />
          </label>

          <label className="full-width">
            Description
            <textarea
              value={formData.description ?? ""}
              onChange={(event) =>
                updateField(
                  "description",
                  event.target.value
                )
              }
              rows={3}
            />
          </label>

          <button
            className="primary-button"
            type="submit"
            disabled={isCreating}
          >
            {isCreating ? "Creating..." : "Create Project"}
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Registered Projects</h2>

        {isLoading ? (
          <p>Loading projects...</p>
        ) : projects.length === 0 ? (
          <p>No projects have been created.</p>
        ) : (
          <div className="card-grid">
            {projects.map((project) => (
              <article
                className="dashboard-card"
                key={project.id}
              >
                <h3>{project.name}</h3>

                <p>
                  {project.description ||
                    "No project description was provided."}
                </p>

                <p>
                  <strong>Problem:</strong>{" "}
                  {project.problem_type}
                </p>

                <p>
                  <strong>Target:</strong>{" "}
                  {project.target_column}
                </p>

                <p>
                  <strong>Priority metric:</strong>{" "}
                  {project.metric_priority}
                </p>

                <p>
                  <strong>Owner:</strong>{" "}
                  {project.owner || "Not specified"}
                </p>

                <small>Project ID: {project.id}</small>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}