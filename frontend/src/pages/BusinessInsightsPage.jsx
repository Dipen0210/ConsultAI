import React, { useMemo, useRef, useState } from "react";
import API from "../utils/api";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
  BarChart,
  Bar,
  LabelList,
} from "recharts";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export default function BusinessInsightsPage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const reportRef = useRef(null);
  const consultantSummary = useMemo(
    () => formatConsultantSummary(result?.gpt_summary ?? ""),
    [result?.gpt_summary]
  );

  const handleFileChange = (event) => {
    setFile(event.target.files[0] ?? null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      alert("Please select a CSV file first.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("kpi_file", file);

    try {
      const response = await API.post("/business-insights", formData);
      setResult(response.data?.data ?? null);
    } catch (error) {
      console.error("Business insights request failed", error);
      alert("Error analyzing business data.");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value ?? 0);

  const formatPercentage = (value) =>
    value === undefined || value === null
      ? "N/A"
      : `${(Number(value) * 100).toFixed(1)}%`;

  const clusterData =
    result?.chart_data?.cluster_scatter?.map((item) => ({
      x: item.x ?? item.profit_margin ?? 0,
      y: item.y ?? item.revenue ?? 0,
      cluster: item.cluster ?? 0,
    })) ?? [];
  const clusterSeries = useMemo(() => {
    const palette = ["#6366f1", "#0ea5e9", "#f97316", "#10b981", "#a855f7"];
    const groups = clusterData.reduce((acc, point) => {
      const key = point.cluster ?? 0;
      if (!acc[key]) acc[key] = [];
      acc[key].push(point);
      return acc;
    }, {});
    return Object.entries(groups).map(([clusterId, points], index) => ({
      clusterId,
      points,
      color: palette[index % palette.length],
    }));
  }, [clusterData]);

  const trendData = result?.chart_data?.trend_data ?? [];

  const segmentData = result?.chart_data?.segment_breakdown ?? [];
  const categoryData = result?.chart_data?.category_breakdown ?? [];
  const regionData = result?.chart_data?.region_breakdown ?? [];
  const productLeaders = result?.chart_data?.product_leaders ?? [];

  const forecastChartData =
    result?.forecast_data?.dates?.map((date, idx) => ({
      period: date,
      revenue: result.forecast_data.revenue_forecast[idx],
    })) ?? [];

  const handleDownloadReport = async () => {
    if (!result) return;
    setDownloading(true);
    try {
      const topSegment = segmentData[0]
        ? `${segmentData[0].label} (${formatCurrency(segmentData[0].revenue)})`
        : "N/A";
      const topCategory = categoryData[0]
        ? `${categoryData[0].label} (${formatCurrency(categoryData[0].revenue)})`
        : "N/A";
      const topRegion = regionData[0]
        ? `${regionData[0].label} (${formatCurrency(regionData[0].revenue)})`
        : "N/A";

      const highlights = [
        `Top segment: ${topSegment}`,
        `Top category: ${topCategory}`,
        `Top region: ${topRegion}`,
      ];

      const payload = {
        company_name: file?.name?.replace(/\.csv$/i, "") || "Uploaded Dataset",
        summary: result.gpt_summary,
        highlights,
        metrics: {
          "Total Revenue": formatCurrency(result.kpi_summary.total_revenue),
          "Avg Profit Margin": formatPercentage(result.kpi_summary.avg_profit_margin),
          "Companies Analysed": result.kpi_summary.num_companies,
        },
        generated_at: new Date().toISOString(),
        action_items: result.alerts?.map((alert) => alert.description) ?? [],
        chart_data: result.chart_data,
        clusters: result.clusters,
        alerts: result.alerts,
      };

      const section = reportRef.current;
      if (!section) {
        throw new Error("Unable to locate report section.");
      }

      const canvas = await html2canvas(section, { scale: 2, useCORS: true });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      let heightLeft = pdfHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
      heightLeft -= pdf.internal.pageSize.getHeight();

      while (heightLeft > 0) {
        position = heightLeft - pdfHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
        heightLeft -= pdf.internal.pageSize.getHeight();
      }

      pdf.save(
        `${(file?.name?.replace(/\.csv$/i, "") || "consultai-insights")
          .toLowerCase()
          .replace(/\s+/g, "-")}-business-insights.pdf`
      );
    } catch (error) {
      console.error("Report generation failed", error);
      alert("Unable to generate PDF report.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">
          Business Performance Insights 📊
        </h2>
        <p className="mt-2 text-slate-600">
          Upload a KPI snapshot to uncover clusters, trends, and actionable
          opportunities.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-3 sm:flex-row">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </form>
        <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 px-4 py-3 text-sm text-slate-600">
          <p className="text-sm font-semibold text-slate-800">
            Tip: richer uploads unlock better insights
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              Include core columns like <span className="font-medium">revenue, profit, profit_margin, segment/category, region, date, churn</span>{" "}
              so the advisor can build clusters and trends.
            </li>
            <li>
              Keep the file clean (one row per record, consistent currency, no merged cells) and save as UTF-8 CSV for the best results.
            </li>
            <li>
              Add recent periods and all key business lines—missing data limits the recommendations surfaced on this page.
            </li>
          </ul>
        </div>
      </section>

      {result && (
        <section className="space-y-6" ref={reportRef}>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              title="Total Revenue"
              value={formatCurrency(result.kpi_summary.total_revenue)}
            />
            <KpiCard
              title="Avg Profit Margin"
              value={formatPercentage(result.kpi_summary.avg_profit_margin)}
            />
            <KpiCard
              title="Avg Churn"
              value={
                result.kpi_summary.avg_churn !== null &&
                result.kpi_summary.avg_churn !== undefined
                  ? formatPercentage(result.kpi_summary.avg_churn)
                  : "N/A"
              }
            />
            <KpiCard
              title="Companies Analysed"
              value={result.kpi_summary.num_companies}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartCard
              title="Cluster Analysis"
              description="Profit margin versus revenue clusters"
            >
              <ResponsiveContainer width="100%" height={320}>
                <ScatterChart margin={{ top: 16, right: 24, left: 0, bottom: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    name="Profit Margin"
                    tickFormatter={(value) => formatPercentage(value)}
                    tick={{ fontSize: 12, fill: "#475569" }}
                    label={{ value: "Profit margin", position: "insideBottom", offset: -8 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    name="Revenue"
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 12, fill: "#475569" }}
                    label={{ value: "Revenue", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip content={(props) => renderClusterTooltip(props, formatCurrency, formatPercentage)} />
                  <Legend
                    verticalAlign="top"
                    align="right"
                    wrapperStyle={{ fontSize: 12, paddingBottom: 8 }}
                  />
                  {clusterSeries.map(({ clusterId, points, color }) => (
                    <Scatter
                      key={`cluster-${clusterId}`}
                      name={`Cluster ${clusterId}`}
                      data={points}
                      fill={color}
                      fillOpacity={0.75}
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Revenue Trend"
              description="Trailing monthly revenue and profit"
            >
              <ResponsiveContainer width="100%" height={320}>
                <LineChart
                  data={trendData}
                  margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="profit"
                    name="Profit"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <BreakdownChart
              title="Revenue by Segment"
              data={segmentData}
              barColor="#6366f1"
              formatCurrency={formatCurrency}
            />
            <BreakdownChart
              title="Revenue by Category"
              data={categoryData}
              barColor="#f97316"
              formatCurrency={formatCurrency}
            />
            <BreakdownChart
              title="Revenue by Region"
              data={regionData}
              barColor="#0ea5e9"
              formatCurrency={formatCurrency}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartCard
              title="Top Products"
              description="Highest revenue and profit contributors"
            >
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold text-slate-600">
                        Product
                      </th>
                      <th className="px-4 py-2 text-right font-semibold text-slate-600">
                        Revenue
                      </th>
                      <th className="px-4 py-2 text-right font-semibold text-slate-600">
                        Profit
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {productLeaders.map((item) => (
                      <tr key={item.product}>
                        <td className="px-4 py-2 text-slate-800">{item.product}</td>
                        <td className="px-4 py-2 text-right text-slate-700">
                          {formatCurrency(item.revenue)}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-700">
                          {formatCurrency(item.profit)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ChartCard>

            <ChartCard
              title="Revenue Forecast"
              description="Projected revenue across the next 12 periods"
            >
              <ResponsiveContainer width="100%" height={320}>
                <LineChart
                  data={forecastChartData}
                  margin={{ top: 16, right: 24, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {result.clusters?.length ? (
            <ChartCard
              title="Cluster Summary"
              description="Average performance metrics per cluster"
            >
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold text-slate-600">
                        Cluster
                      </th>
                      <th className="px-4 py-2 text-right font-semibold text-slate-600">
                        Avg Profit
                      </th>
                      <th className="px-4 py-2 text-right font-semibold text-slate-600">
                        Profit Margin
                      </th>
                      <th className="px-4 py-2 text-right font-semibold text-slate-600">
                        Members
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {result.clusters.map((cluster) => (
                      <tr key={cluster.cluster}>
                        <td className="px-4 py-2 text-slate-800">
                          Cluster {cluster.cluster}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-700">
                          {formatCurrency(cluster.avg_profit)}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-700">
                          {formatPercentage(cluster.avg_profit_margin)}
                        </td>
                        <td className="px-4 py-2 text-right text-slate-700">
                          {cluster.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ChartCard>
          ) : null}

          {result.alerts?.length ? (
            <ChartCard
              title="Alerts"
              description="Potential risks and optimisation opportunities"
              className="bg-amber-50 border border-amber-200"
            >
              <ul className="space-y-3">
                {result.alerts.map((alert, idx) => (
                  <li
                    key={`${alert.title}-${idx}`}
                    className="flex flex-col rounded-xl bg-white/80 p-3 shadow-sm"
                  >
                    <span className="font-semibold text-slate-800">
                      {alert.title}
                    </span>
                    <span className="text-sm text-slate-600">
                      {alert.description}
                    </span>
                    <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-700">
                      {alert.discount !== undefined && (
                        <span>Discount: {alert.discount.toFixed(2)}</span>
                      )}
                      {alert.profit !== undefined && (
                        <span>Profit: {formatCurrency(alert.profit)}</span>
                      )}
                      {alert.profit_margin !== undefined && (
                        <span>Margin: {formatPercentage(alert.profit_margin)}</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </ChartCard>
          ) : null}

          <div className="rounded-3xl bg-slate-100 p-6">
            <h3 className="text-lg font-semibold text-slate-800">
              Consultant Recommendation
            </h3>
            <div className="mt-2 text-slate-700 leading-relaxed space-y-2">
              {consultantSummary.intro.length === 0 &&
              consultantSummary.bullets.length === 0 ? (
                <p>{result.gpt_summary}</p>
              ) : (
                <>
                  {consultantSummary.intro.map((line, idx) => (
                    <p key={`summary-intro-${idx}`}>{line}</p>
                  ))}
                  {consultantSummary.bullets.length > 0 && (
                    <div className="space-y-1 text-sm">
                      {consultantSummary.bullets.map((line, idx) => (
                        <div
                          key={`summary-bullet-${idx}`}
                          className="flex items-start gap-2"
                        >
                          <span className="text-indigo-500 leading-6">•</span>
                          <span className="flex-1">{line}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
            {(result.gpt_summary_source || result.gpt_summary_warning) && (
              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                {result.gpt_summary_source && (
                  <span>
                    Source:{" "}
                    {result.gpt_summary_source === "huggingface"
                      ? "Live agent"
                      : "Heuristic fallback"}
                  </span>
                )}
                {result.gpt_summary_warning && (
                  <span className="text-amber-600">
                    {result.gpt_summary_warning}
                  </span>
                )}
              </div>
            )}
            <button
              type="button"
              onClick={handleDownloadReport}
              className="mt-3 inline-flex items-center rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={downloading}
            >
              {downloading ? "Preparing report..." : "Download PDF Report"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

function KpiCard({ title, value }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-600">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function ChartCard({ title, description, children, className = "" }) {
  return (
    <div className={`rounded-3xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        {description ? <p className="text-sm text-slate-600">{description}</p> : null}
      </div>
      {children}
    </div>
  );
}

function BreakdownChart({ title, data, barColor, formatCurrency }) {
  return (
    <ChartCard title={title}>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical" margin={{ left: 48 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
          <YAxis type="category" dataKey="label" />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Bar dataKey="revenue" fill={barColor} radius={[4, 4, 4, 4]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function formatConsultantSummary(text) {
  if (!text) {
    return { intro: [], bullets: [] };
  }
  const normalized = text
    .replace(/\s*\*\s+/g, "\n• ")
    .replace(/\*\*/g, "")
    .trim();
  const lines = normalized
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
  const intro = [];
  const bullets = [];
  lines.forEach((line) => {
    if (line.startsWith("• ")) {
      bullets.push(line.slice(2).trim());
    } else {
      intro.push(line);
    }
  });
  return { intro, bullets };
}

function renderClusterTooltip(props, formatCurrency, formatPercentage) {
  const { active, payload } = props ?? {};
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  const point = payload[0]?.payload;
  if (!point) {
    return null;
  }
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">
        Cluster {point.cluster ?? "–"}
      </p>
      <p>Profit margin: {formatPercentage(point.x)}</p>
      <p>Revenue: {formatCurrency(point.y)}</p>
    </div>
  );
}
