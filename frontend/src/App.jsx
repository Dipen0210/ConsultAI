import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import NotFound from "./pages/NotFound";
import MarketEntry from "./pages/MarketEntry";
import BusinessInsightsPage from "./pages/BusinessInsightsPage";
import AdvisorPage from "./pages/AdvisorPage";
import HealthCheck from "./components/HealthCheck";
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/market-entry" element={<MarketEntry />} />
            <Route path="/business-insights" element={<BusinessInsightsPage />} />
            <Route path="/advisor" element={<AdvisorPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <footer className="mx-auto max-w-6xl px-6 pb-10">
          <HealthCheck />
        </footer>
      </div>
    </BrowserRouter>
  );
}
