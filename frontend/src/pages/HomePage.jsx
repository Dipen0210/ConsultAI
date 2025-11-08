import React from "react";
import { Link } from "react-router-dom";

const shortcuts = [
  {
    to: "/market-entry",
    title: "Market Entry Advisor",
    description: "Score and rank expansion markets with weighted KPIs.",
    accent: "from-brand-500 to-brand-600",
  },
  {
    to: "/business-insights",
    title: "Business Insights",
    description: "Upload KPI data to uncover clusters and forecasts.",
    accent: "from-emerald-500 to-emerald-600",
  },
  {
    to: "/advisor",
    title: "AI Consultant",
    description: "Ask strategic questions and get expert bullet insights.",
    accent: "from-amber-500 to-amber-600",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-bold md:text-4xl">Welcome to ConsultAI 🧠</h1>
        <p className="mt-4 max-w-3xl text-lg text-slate-600">
          Your data-driven consulting companion for market entry strategy,
          operational insights, and executive-ready reporting. Explore the
          modules below to analyze opportunities and craft confident strategic
          decisions.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-slate-800">Quick Actions</h2>
        <p className="mt-2 text-slate-600">
          Jump into any workflow with a single click.
        </p>
        <div className="mt-6 grid gap-6 sm:grid-cols-2 md:grid-cols-3">
          {shortcuts.map((shortcut) => (
            <Link
              key={shortcut.to}
              to={shortcut.to}
              className={`group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-transform hover:-translate-y-1`}
            >
              <div
                className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${shortcut.accent}`}
              />
              <h3 className="text-xl font-semibold text-slate-900">
                {shortcut.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{shortcut.description}</p>
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-brand-500">
                Open workflow
                <span className="transition-transform group-hover:translate-x-1">→</span>
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
