import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import {
  FiActivity,
  FiDatabase,
  FiFolder,
  FiGrid,
  FiMenu,
  FiPackage,
  FiServer,
  FiX,
} from "react-icons/fi";

const navigationItems = [
  {
    to: "/",
    label: "Dashboard",
    icon: FiGrid,
    end: true,
  },
  {
    to: "/projects",
    label: "Projects",
    icon: FiFolder,
  },
  {
    to: "/models",
    label: "Model Registry",
    icon: FiPackage,
  },
  {
    to: "/datasets",
    label: "Datasets",
    icon: FiDatabase,
  },
  {
    to: "/predictions",
    label: "Prediction Logs",
    icon: FiServer,
  },
  {
    to: "/health",
    label: "Model Health",
    icon: FiActivity,
  },
  {
    to: "/jobs",
    label: "Automation Jobs",
    icon: FiActivity,
  },
];

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <button
        className="mobile-menu-button"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open navigation"
      >
        <FiMenu />
      </button>

      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-open" : ""
        }`}
      >
        <div className="brand-row">
          <div>
            <strong>ModelOps Doctor</strong>
            <small>ML Health Clinic</small>
          </div>

          <button
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <FiX />
          </button>
        </div>

        <nav className="sidebar-navigation">
          {navigationItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  isActive
                    ? "navigation-link active"
                    : "navigation-link"
                }
              >
                <Icon />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}