"""Fetch country-level indicators from the World Bank API."""

from __future__ import annotations

import pathlib
from typing import Dict, List

import pandas as pd
import requests

YEAR = "2022"
PER_PAGE = 400
REQUIRED_COLUMNS = [
    "Country",
    "ISO3",
    "Region",
    "Income_Level",
    "GDP_Growth",
    "Inflation",
    "Internet_Penetration",
    "Population",
]


def _load_country_metadata() -> Dict[str, Dict[str, str]]:
    """Return a mapping of ISO3 → metadata for actual countries."""
    url = f"https://api.worldbank.org/v2/country?format=json&per_page={PER_PAGE}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    entries = payload[1]

    metadata: Dict[str, Dict[str, str]] = {}
    for entry in entries:
        region = entry.get("region", {}) or {}
        if region.get("id") == "NA":
            continue  # skip aggregates
        iso3 = entry.get("id")
        if not iso3:
            continue
        metadata[iso3] = {
            "Country": entry.get("name"),
            "ISO3": iso3,
            "Region": region.get("value") or "",
            "Income_Level": entry.get("incomeLevel", {}).get("value") or "",
        }
    return metadata


def fetch_worldbank_data(
    indicator_code: str,
    name: str,
    metadata: Dict[str, Dict[str, str]],
    *,
    include_meta: bool = False,
) -> pd.DataFrame:
    """Fetch data for a single indicator and return a DataFrame."""
    url = (
        "https://api.worldbank.org/v2/country/all/indicator/"
        f"{indicator_code}?format=json&per_page={PER_PAGE}&date={YEAR}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    data: List[Dict[str, object]] = payload[1]  # payload[1] contains results

    rows: List[Dict[str, object]] = []
    for entry in data:
        value = entry.get("value")
        if value is None:
            continue
        iso3 = (entry.get("countryiso3code") or "").strip()
        if not iso3 or iso3 not in metadata:
            continue
        country_meta = metadata[iso3]
        row = {"Country": country_meta["Country"], name: value}
        if include_meta:
            row.update(
                {
                    "ISO3": country_meta["ISO3"],
                    "Region": country_meta["Region"],
                    "Income_Level": country_meta["Income_Level"],
                }
            )
        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    print("Fetching data from World Bank...")

    metadata = _load_country_metadata()

    gdp = fetch_worldbank_data(
        "NY.GDP.MKTP.KD.ZG",
        "GDP_Growth",
        metadata,
        include_meta=True,
    )
    inflation = fetch_worldbank_data(
        "FP.CPI.TOTL.ZG",
        "Inflation",
        metadata,
    )
    internet = fetch_worldbank_data(
        "IT.NET.USER.ZS",
        "Internet_Penetration",
        metadata,
    )
    population = fetch_worldbank_data(
        "SP.POP.TOTL",
        "Population",
        metadata,
    )

    # Merge all indicators
    df = (
        gdp.merge(inflation, on="Country", how="outer")
        .merge(internet, on="Country", how="outer")
        .merge(population, on="Country", how="outer")
    )

    # Clean + filter
    df = df.dropna(subset=["GDP_Growth", "Inflation"])
    df["Population_Millions"] = df["Population"] / 1e6

    # Select column order for readability
    ordered_columns = [col for col in REQUIRED_COLUMNS if col in df.columns] + [
        "Population_Millions"
    ]
    df = df[ordered_columns]

    # Save
    output_path = pathlib.Path(__file__).with_name("market_data.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Saved merged data → {output_path}")


if __name__ == "__main__":
    main()
