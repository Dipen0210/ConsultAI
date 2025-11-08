import React from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home" },
  { to: "/market-entry", label: "Market Entry" },
  { to: "/business-insights", label: "Insights" },
  { to: "/advisor", label: "AI Agent" },
];

const navLinkClass = ({ isActive }) =>
  `rounded-full px-3 py-1 text-sm font-medium transition-colors ${
    isActive
      ? "bg-brand-500 text-white shadow"
      : "text-slate-200 hover:text-white hover:bg-slate-700"
  }`;

export default function Navbar() {
  return (
    <header className="bg-slate-900 text-white shadow-sm">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 md:flex-row md:items-center md:justify-between">
        <NavLink to="/" className="text-2xl font-semibold">
          ConsultAI
        </NavLink>
        <nav className="flex flex-wrap items-center gap-3">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} className={navLinkClass}>
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
