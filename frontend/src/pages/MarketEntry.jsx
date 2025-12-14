import React, { useState } from "react";
import API from "../utils/api";
import MarketResultCard from "../components/MarketResultCard";

const defaultForm = {
  industry: "",
  business_model: "",
  presence_mode: "",
  target_market: "",
  risk_profile: "",
  customer_type: "",
  region: "",
  capital: "",
};

const industryOptions = [
  { value: "Agriculture", label: "Agriculture", hint: "Farming, livestock, agri-tech" },
  { value: "Manufacturing", label: "Manufacturing", hint: "Cars, electronics, furniture" },
  { value: "Retail", label: "Retail", hint: "Omni-channel stores like Walmart, Amazon" },
  { value: "Technology", label: "Technology", hint: "Software, AI, cybersecurity, cloud" },
  { value: "Healthcare", label: "Healthcare", hint: "Hospitals, pharma, medical devices" },
  { value: "Finance", label: "Finance", hint: "Banks, investment firms, fintech" },
  { value: "Energy", label: "Energy", hint: "Oil, renewables, utilities" },
  { value: "Transportation & Logistics", label: "Transportation & Logistics", hint: "Shipping, freight, last-mile delivery" },
  { value: "Education", label: "Education", hint: "Schools, ed-tech platforms" },
  { value: "Hospitality", label: "Hospitality", hint: "Hotels, travel, restaurants" },
  { value: "Construction & Real Estate", label: "Construction & Real Estate", hint: "Builders, brokers, prop-tech" },
  { value: "Entertainment & Media", label: "Entertainment & Media", hint: "Movies, gaming, sports, streaming" },
  { value: "Professional Services", label: "Professional Services", hint: "Legal, consulting, accounting" },
];

const businessModelOptions = [
  { value: "Product-based", label: "Product-based", hint: "Sells physical goods" },
  { value: "Service-based", label: "Service-based", hint: "Delivers services like consulting or repair" },
  { value: "Subscription", label: "Subscription", hint: "Recurring revenue (SaaS, media)" },
  { value: "Marketplace", label: "Marketplace", hint: "Connects buyers & sellers (Uber, Airbnb)" },
  { value: "Franchise", label: "Franchise", hint: "Operate under an existing brand" },
  { value: "Dropshipping", label: "Dropshipping", hint: "Sell without holding inventory" },
  { value: "Licensing/IP", label: "Licensing/IP", hint: "Monetize content or technology rights" },
  { value: "Manufacturing", label: "Manufacturing model", hint: "Produce goods and sell directly" },
  { value: "Brokerage", label: "Brokerage", hint: "Charge per transaction (Robinhood, brokers)" },
];

const presenceModes = ["Digital", "Physical", "Hybrid"];

const targetMarkets = ["Mass Market", "Niche", "Premium", "Budget"];

const riskProfiles = ["Low", "Medium", "High"];

const customerTypes = [
  { value: "B2C", label: "B2C (Business → Consumer)", hint: "e.g., Amazon, Netflix, Nike" },
  { value: "B2B", label: "B2B (Business → Business)", hint: "e.g., Salesforce, IBM, consulting firms" },
  { value: "B2G", label: "B2G (Business → Government)", hint: "e.g., defense or infra contractors" },
  { value: "C2C", label: "C2C (Consumer → Consumer)", hint: "e.g., eBay, Facebook Marketplace" },
  { value: "B2B2C", label: "B2B2C (Hybrid)", hint: "e.g., Shopify, embedded marketplace models" },
];

const regionOptions = [
  "East Asia & Pacific",
  "Europe & Central Asia",
  "Latin America & Caribbean",
  "Middle East, North Africa, Afghanistan & Pakistan",
  "North America",
  "South Asia",
  "Sub-Saharan Africa",
];

const regionDescriptions = {
  "East Asia & Pacific": "High-growth mix of developed (Singapore) and emerging (Vietnam) digital economies.",
  "Europe & Central Asia": "Mature markets with high internet usage and stable institutions.",
  "Latin America & Caribbean": "Rapidly urbanizing regions with growing middle class demand.",
  "Middle East, North Africa, Afghanistan & Pakistan": "Energy-rich and youthful populations; inflation varies widely.",
  "North America": "Large, high-income markets with intense competition.",
  "South Asia": "Scale-driven markets led by India, Bangladesh, Pakistan.",
  "Sub-Saharan Africa": "Frontier markets with fast population growth and rising mobile adoption.",
};

const weightNarrativeLabels = {
  GDP_Growth: "GDP growth momentum",
  Inflation: "inflation stability",
  Internet_Penetration: "digital readiness",
  Population_Millions: "population scale",
  corruption_index_corruption: "governance risk",
  cost_index_cost_of_living: "operating cost index",
  purchasing_power_index_cost_of_living: "consumer purchasing power",
};

const weightDisplayLabels = {
  GDP_Growth: "GDP growth",
  Inflation: "Inflation",
  Internet_Penetration: "Digital reach",
  Population_Millions: "Population",
  corruption_index_corruption: "Governance",
  cost_index_cost_of_living: "Cost base",
  purchasing_power_index_cost_of_living: "Purchasing power",
};

const getWeightDisplayLabel = (metric) =>
  weightDisplayLabels[metric] || metric.replaceAll("_", " ");

const describeWeights = (weights) => {
  if (!weights) return "";
  const parts = Object.entries(weights)
    .map(([key, value]) => {
      const label = weightNarrativeLabels[key] || key;
      return `${label} (~${(value * 100).toFixed(0)}%)`;
    })
    .join(", ");
  return `Scores balance ${parts}, meaning countries with stronger readings on those metrics rise to the top while inflation is inverted to reward stability.`;
};

const formatRawValue = (metric, value) => {
  if (metric === "Population_Millions") {
    return `${value.toFixed(1)}M`;
  }
  if (metric === "Internet_Penetration") {
    return `${value.toFixed(1)}%`;
  }
  if (metric === "Inflation") {
    return `${value.toFixed(2)}%`;
  }
  if (metric === "purchasing_power_index_cost_of_living") {
    return `${value.toFixed(1)} index`;
  }
  if (metric === "cost_index_cost_of_living") {
    return `${value.toFixed(1)} index`;
  }
  if (metric === "corruption_index_corruption") {
    return `${value.toFixed(1)}`;
  }
  return value.toFixed(2);
};

export default function MarketEntry() {
  const [formData, setFormData] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setResults(null);
    setError(null);

    const payload = {
      industry: formData.industry,
      business_model: formData.business_model,
      presence_mode: formData.presence_mode,
      target_market: formData.target_market,
      risk_profile: formData.risk_profile,
      customer_type: formData.customer_type,
      regions: formData.region ? [formData.region] : [],
      capital: formData.capital ? Number(formData.capital) : 0,
    };

    try {
      const response = await API.post("/market-entry", payload);
      setResults(response.data?.data ?? null);
    } catch (err) {
      const message =
        err.response?.data?.message || "Unable to analyze markets right now.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          🌍 Market Entry Strategy Advisor
        </h1>
        <p className="mt-2 text-slate-600">
          Describe your business profile and we will automatically weigh growth,
          risk, digital readiness, and scale indicators to highlight the best
          expansion markets.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-2"
      >
        <div>
          <label className="text-sm font-medium text-slate-700">Industry</label>
          <select
            name="industry"
            value={formData.industry}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select industry</option>
            {industryOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Business Model
          </label>
          <select
            name="business_model"
            value={formData.business_model}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select business model</option>
            {businessModelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Presence Mode
          </label>
          <select
            name="presence_mode"
            value={formData.presence_mode}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select presence</option>
            {presenceModes.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Target Market
          </label>
          <select
            name="target_market"
            value={formData.target_market}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select target market</option>
            {targetMarkets.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Risk Profile
          </label>
          <select
            name="risk_profile"
            value={formData.risk_profile}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select risk tolerance</option>
            {riskProfiles.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Focus Region
          </label>
          <select
            name="region"
            value={formData.region}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          >
            <option value="">All regions</option>
            {regionOptions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Customer Type
          </label>
          <select
            name="customer_type"
            value={formData.customer_type}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            required
          >
            <option value="">Select customer type</option>
            {customerTypes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">
            Available Capital (USD)
          </label>
          <input
            type="number"
            name="capital"
            value={formData.capital}
            onChange={handleChange}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="e.g. 10000000"
            min="0"
          />
        </div>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 font-semibold text-white shadow hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300 md:w-auto"
          >
            {loading ? "Analyzing..." : "Analyze Market Entry"}
          </button>
        </div>
      </form>

      <div className="grid gap-4 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            2) By sector / industry
          </p>
          <p className="text-xs text-slate-500">What the business does</p>
          <dl className="mt-2 space-y-2 text-sm text-slate-600">
            {industryOptions.map((option) => (
              <div key={option.value}>
                <dt className="font-medium text-slate-900">{option.label}</dt>
                <dd className="text-slate-600">{option.hint}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            3) By business model
          </p>
          <p className="text-xs text-slate-500">How the business makes money</p>
          <dl className="mt-2 space-y-2 text-sm text-slate-600">
            {businessModelOptions.map((option) => (
              <div key={option.value}>
                <dt className="font-medium text-slate-900">{option.label}</dt>
                <dd className="text-slate-600">{option.hint}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            1) By customer type
          </p>
          <dl className="mt-2 space-y-2 text-sm text-slate-600">
            {customerTypes.map((type) => (
              <div key={type.value}>
                <dt className="font-medium text-slate-900">{type.label}</dt>
                <dd className="text-slate-600">{type.hint}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">
            4) By region focus
          </p>
          <p className="text-xs text-slate-500">Where expansion is targeted</p>
          <dl className="mt-2 space-y-2 text-sm text-slate-600">
            {regionOptions.map((region) => (
              <div key={region}>
                <dt className="font-medium text-slate-900">{region}</dt>
                <dd className="text-slate-600">
                  {regionDescriptions[region]}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {results && (
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              Recommended Markets
            </h2>
            <p className="text-sm text-slate-500">
              Weighted using GDP growth, inflation stability, digital adoption,
              and population scale.
            </p>
          </div>
          <div className="space-y-3">
            {results.top_markets?.map((entry, index) => (
              <MarketResultCard
                key={entry.Country}
                country={entry.Country}
                score={entry.Score}
                rank={index + 1}
              />
            ))}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700">Weights used</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {results.weights_used &&
                Object.entries(results.weights_used)
                  .sort((a, b) => b[1] - a[1])
                  .map(([metric, value]) => {
                    const displayLabel = getWeightDisplayLabel(metric);
                    const helperText = weightNarrativeLabels[metric];
                    const percentage = (value * 100).toFixed(1);
                    const barWidth = Math.min(Math.max(value * 100, 6), 100);
                    return (
                      <div
                        key={metric}
                        className="rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm"
                      >
                        <div className="flex items-center justify-between text-sm text-slate-900">
                          <span>{displayLabel}</span>
                          <span>{percentage}%</span>
                        </div>
                        <div className="mt-2 h-2 rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-indigo-500"
                            style={{ width: `${barWidth}%` }}
                          />
                        </div>
                        {helperText && (
                          <p className="mt-2 text-xs text-slate-500">
                            {helperText}
                          </p>
                        )}
                      </div>
                    );
                  })}
            </div>
          </div>
          {results.metric_breakdown && (
            <div>
              <p className="text-sm font-medium text-slate-700">
                Top market metric breakdown
              </p>
              <div className="mt-3 space-y-5">
                {results.metric_breakdown.map((entry) => (
                  <div
                    key={entry.country}
                    className="rounded-2xl border border-slate-200 bg-white/80 px-5 py-4 shadow-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-slate-900 text-lg">
                        {entry.country}
                      </p>
                      <span className="text-sm text-indigo-600">
                        Score {(entry.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {Object.entries(entry.metrics).map(([metric, detail]) => {
                        const label = getWeightDisplayLabel(metric);
                        const contribution = (detail.contribution * 100).toFixed(1);
                        const isZero = Number(contribution) === 0;
                        return (
                          <div
                            key={metric}
                            className="rounded-xl border border-slate-200 bg-slate-50/60 p-3 text-sm"
                          >
                            <div className="flex items-center justify-between text-slate-900">
                              <span>{label}</span>
                              <span
                                className={`text-xs ${
                                  isZero ? "text-slate-400" : "text-emerald-600"
                                }`}
                              >
                                {contribution}%
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-slate-500">
                              Raw {formatRawValue(metric, detail.raw)}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <p className="text-slate-700">{results.summary}</p>
          {(results.explainable_summary || results.weights_used) && (
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/80 px-5 py-4 text-sm text-slate-700 shadow-sm">
              <div className="flex items-center justify-between gap-2">
                <p className="text-base font-semibold text-slate-900">
                  How this decision was made
                </p>
                {results.explainable_summary_source && (
                  <span className="rounded-full border border-indigo-200 bg-white/80 px-3 py-1 text-xs font-medium text-indigo-700">
                    {results.explainable_summary_source === "huggingface"
                      ? "Live agent"
                      : "Heuristic fallback"}
                  </span>
                )}
              </div>
              <div className="mt-3 space-y-2">
                {(results.explainable_summary ||
                  describeWeights(results.weights_used))
                  .split(/\n+/)
                  .filter((line) => line.trim().length > 0)
                  .map((line, index) => {
                    const cleaned = line.replace(/^\s*•\s*/, "");
                    return (
                      <div
                        key={`explain-line-${index}`}
                        className="flex items-start gap-3 leading-relaxed"
                      >
                        <span className="text-indigo-400 font-semibold">•</span>
                        <p className="flex-1 whitespace-pre-line text-slate-800">
                          {cleaned}
                        </p>
                      </div>
                    );
                  })}
              </div>
              {results.explainable_summary_warning && (
                <p className="mt-3 text-xs text-amber-600">
                  {results.explainable_summary_warning}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
