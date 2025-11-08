import React from "react";

export default function MarketResultCard({ country, score, rank, summary }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div>
        <p className="font-semibold text-slate-900">
          {rank ? `${rank}. ${country}` : country}
        </p>
        {summary && <p className="text-sm text-slate-500">{summary}</p>}
      </div>
      <span className="text-lg font-bold text-emerald-600">
        {(score * 100).toFixed(1)}%
      </span>
    </div>
  );
}
