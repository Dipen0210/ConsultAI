from flask import Blueprint, jsonify, request

try:
    from backend.services.business_insights import (
        build_alerts,
        build_cluster_payload,
        build_dimension_insights,
        build_forecast,
        build_kpi_summary,
        build_trend_data,
        detect_columns,
        identify_numeric_columns,
        load_dataframe,
        resolve_series,
    )
except ImportError:  # pragma: no cover - fallback for script usage
    from services.business_insights import (
        build_alerts,
        build_cluster_payload,
        build_dimension_insights,
        build_forecast,
        build_kpi_summary,
        build_trend_data,
        detect_columns,
        identify_numeric_columns,
        load_dataframe,
        resolve_series,
    )

business_insights_bp = Blueprint("business_insights", __name__)


@business_insights_bp.route("/api/business-insights", methods=["POST"])
def business_insights():
    if request.content_type and "multipart/form-data" not in request.content_type:
        return (
            jsonify({"status": "error", "message": "Content-Type must be multipart/form-data."}),
            400,
        )

    try:
        df = load_dataframe(request)
        print("Uploaded columns:", df.columns.tolist())

        numeric_cols, numeric_cache = identify_numeric_columns(df)
        if len(numeric_cols) < 2:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Not enough numeric columns for analysis.",
                    }
                ),
                400,
            )

        mapping = detect_columns(df)
        detected = resolve_series(df, mapping, numeric_cols, numeric_cache)

        cluster_payload = build_cluster_payload(
            detected.revenue,
            detected.profit,
            detected.profit_margin,
        )
        forecast_data = build_forecast(detected.revenue)
        kpi_summary = build_kpi_summary(df, mapping, detected)
        dimension_insights = build_dimension_insights(df, mapping, detected)
        trend_data = build_trend_data(df, mapping, detected)
        alerts = build_alerts(df, mapping, detected, numeric_cache)

        top_segment = dimension_insights["segments"][0]["label"] if dimension_insights["segments"] else None
        top_region = dimension_insights["regions"][0]["label"] if dimension_insights["regions"] else None
        summary_parts = []
        if top_segment:
            summary_parts.append(f"{top_segment} leads revenue contribution.")
        if top_region:
            summary_parts.append(f"Strongest geographic performance observed in {top_region}.")
        summary_parts.append(
            "Revenue and profit margin analysis completed. Higher-margin clusters show strong sales performance."
        )
        if alerts:
            summary_parts.append("Review the flagged discounts and low-margin items for corrective actions.")
        gpt_summary = " ".join(summary_parts)

        response = {
            "status": "success",
            "data": {
                "kpi_summary": kpi_summary,
                "clusters": cluster_payload["clusters"],
                "chart_data": {
                    "cluster_scatter": cluster_payload["cluster_scatter"],
                    "segment_breakdown": dimension_insights["segments"],
                    "category_breakdown": dimension_insights["categories"],
                    "region_breakdown": dimension_insights["regions"],
                    "product_leaders": dimension_insights["products"],
                    "trend_data": trend_data,
                },
                "alerts": alerts,
                "forecast_data": forecast_data,
                "gpt_summary": gpt_summary,
            },
            "message": "KPI analysis complete.",
        }
        return jsonify(response), 200

    except ValueError as exc:
        try:
            from flask import current_app

            current_app.logger.warning("Business insights error: %s", exc)
        except Exception:
            pass
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - diagnostic aid
        try:
            from flask import current_app

            current_app.logger.exception("Business insights unexpected error")
        except Exception:
            pass
        return jsonify({"status": "error", "message": str(exc)}), 400
