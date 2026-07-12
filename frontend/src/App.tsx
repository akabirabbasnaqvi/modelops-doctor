import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import AppLayout from "./layouts/AppLayout";

import DashboardPage from "./pages/DashboardPage";
import ProjectsPage from "./pages/ProjectsPage";
import ModelsPage from "./pages/ModelsPage";
import DatasetsPage from "./pages/DatasetsPage";
import PredictionBatchesPage from "./pages/PredictionBatchesPage";
import HealthChecksPage from "./pages/HealthChecksPage";
import JobsPage from "./pages/JobsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={<AppLayout />}
        >
          <Route
            path="/"
            element={<DashboardPage />}
          />

          <Route
            path="/projects"
            element={<ProjectsPage />}
          />

          <Route
            path="/models"
            element={<ModelsPage />}
          />

          <Route
            path="/datasets"
            element={<DatasetsPage />}
          />

          <Route
            path="/predictions"
            element={<PredictionBatchesPage />}
          />

          <Route
            path="/health"
            element={<HealthChecksPage />}
          />

          <Route
            path="/jobs"
            element={<JobsPage />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}