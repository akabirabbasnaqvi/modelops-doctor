import {
  type FormEvent,
  useEffect,
  useState,
} from "react";

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
  const [formData, setFormData] =
    useState<ProjectCreateRequest>(initialFormData);
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
    } catch {
      setError(
        "Projects could not be loaded. Confirm that the backend is running."
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

      setFormData(initialFormData);

      setSuccessMessage(
        `Project "${newProject.name}" was created successfully.`
      );
    } catch (requestError: any) {
      const detail =
        requestError?.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "The project could not be created."
      );
    } finally {
      setIsCreating(false);
    }
  }

  function updateField(
    field: keyof ProjectCreateRequest,
    value: string
  ) {
    setFormData((currentData) => ({
      ...currentData,
      [field]: value,
    }));
  }

  return (
    <div>
      <div style={{ marginBottom: "30px" }}>
        <h1>Projects</h1>

        <p>
          Create and manage machine-learning monitoring
          workspaces.
        </p>
      </div>

      {error && (
        <div
          style={{
            marginBottom: "20px",
            padding: "14px",
            borderRadius: "8px",
            color: "#991b1b",
            background: "#fee2e2",
          }}
        >
          {error}
        </div>
      )}

      {successMessage && (
        <div
          style={{
            marginBottom: "20px",
            padding: "14px",
            borderRadius: "8px",
            color: "#166534",
            background: "#dcfce7",
          }}
        >
          {successMessage}
        </div>
      )}

      <section
        style={{
          marginBottom: "32px",
          padding: "24px",
          borderRadius: "12px",
          background: "white",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.15)",
        }}
      >
        <h2>Create Project</h2>

        <form
          onSubmit={handleSubmit}
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "18px",
          }}
        >
          <label>
            Project Name
            <input
              required
              minLength={3}
              value={formData.name}
              onChange={(event) =>
                updateField("name", event.target.value)
              }
              style={inputStyle}
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
              style={inputStyle}
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
              style={inputStyle}
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
              style={inputStyle}
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
              style={inputStyle}
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
              style={inputStyle}
            />
          </label>

          <label
            style={{
              gridColumn: "1 / -1",
            }}
          >
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
              style={{
                ...inputStyle,
                resize: "vertical",
              }}
            />
          </label>

          <button
            type="submit"
            disabled={isCreating}
            style={{
              width: "180px",
              padding: "12px 18px",
              border: "none",
              borderRadius: "8px",
              color: "white",
              background: isCreating
                ? "#64748b"
                : "#2563eb",
              cursor: isCreating
                ? "not-allowed"
                : "pointer",
              fontWeight: 600,
            }}
          >
            {isCreating ? "Creating..." : "Create Project"}
          </button>
        </form>
      </section>

      <section>
        <h2>Registered Projects</h2>

        {isLoading ? (
          <p>Loading projects...</p>
        ) : projects.length === 0 ? (
          <p>No projects have been created.</p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "20px",
            }}
          >
            {projects.map((project) => (
              <article
                key={project.id}
                style={{
                  padding: "22px",
                  borderRadius: "12px",
                  background: "white",
                  boxShadow:
                    "0 1px 3px rgba(0, 0, 0, 0.15)",
                }}
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

const inputStyle = {
  boxSizing: "border-box" as const,
  display: "block",
  width: "100%",
  marginTop: "8px",
  padding: "11px 12px",
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  font: "inherit",
  background: "white",
};