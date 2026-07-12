import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
      }}
    >
      <aside
        style={{
          width: "250px",
          padding: "20px",
          background: "#1e293b",
          color: "white",
        }}
      >
        <h2>ModelOps Doctor</h2>

        <nav>
          <div>
            <NavLink to="/">Dashboard</NavLink>
          </div>

          <div>
            <NavLink to="/projects">Projects</NavLink>
          </div>

          <div>
            <NavLink to="/models">Models</NavLink>
          </div>

          <div>
            <NavLink to="/datasets">Datasets</NavLink>
          </div>

          <div>
            <NavLink to="/predictions">
              Predictions
            </NavLink>
          </div>

          <div>
            <NavLink to="/health">
              Health Checks
            </NavLink>
          </div>

          <div>
            <NavLink to="/jobs">Jobs</NavLink>
          </div>
        </nav>
      </aside>

      <main
        style={{
          flex: 1,
          padding: "20px",
        }}
      >
        <Outlet />
      </main>
    </div>
  );
}