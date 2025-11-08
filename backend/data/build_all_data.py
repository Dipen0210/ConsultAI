"""Combine market_data.csv with supplemental indicator CSVs."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
BASE_DATA = BASE_DIR / "market_data.csv"
OUTPUT = BASE_DIR / "all_data.csv"
SUPPLEMENTAL_FILES = {
    "corruption": BASE_DIR / "corruption.csv",
    "cost_of_living": BASE_DIR / "cost_of_living.csv",
    # Tourism and unemployment CSVs exist but are excluded due to limited coverage.
}
ALIASES: Dict[str, str] = {
    "hongkong": "hongkongsarchina",
    "southkorea": "korearep",
    "northkorea": "koreademrep",
    "turkey": "turkiye",
    "egypt": "egyptarabrep",
    "ivorycoast": "cotedivoire",
    "uae": "unitedarabemirates",
    "uk": "unitedkingdom",
}
IMPUTE_COLUMNS = [
    "annual_income_corruption",
    "corruption_index_corruption",
    "cost_index_cost_of_living",
    "monthly_income_cost_of_living",
    "purchasing_power_index_cost_of_living",
]


def _normalize_country(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    key = "".join(ch for ch in name.lower() if ch.isalnum())
    return ALIASES.get(key, key)


def _impute_missing(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        mask = result[column].isna()
        if not mask.any():
            continue
        region_medians = (
            result.loc[~mask, ["Region", column]]
            .groupby("Region")[column]
            .median()
        )
        result.loc[mask, column] = result.loc[mask, "Region"].map(region_medians)
        still_missing = result[column].isna()
        if still_missing.any():
            overall = result[column].median()
            result.loc[still_missing, column] = overall
    return result


def build_dataset() -> pd.DataFrame:
    base = pd.read_csv(BASE_DATA)
    base["country_key"] = base["Country"].map(_normalize_country)

    merged = base.copy()
    for label, path in SUPPLEMENTAL_FILES.items():
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df["country_key"] = df["country"].map(_normalize_country)
        rename_map = {
            col: f"{col}_{label}"
            for col in df.columns
            if col not in {"country", "country_key"}
        }
        df = df.rename(columns=rename_map)
        merged = merged.merge(
            df.drop(columns=["country"]), on="country_key", how="left"
        )

    merged = merged.drop(columns=["country_key"])
    merged = _impute_missing(merged, IMPUTE_COLUMNS)
    return merged


def main() -> None:
    dataset = build_dataset()
    dataset.to_csv(OUTPUT, index=False)
    print(f"✅ Saved merged dataset → {OUTPUT} ({dataset.shape[0]} rows)")


if __name__ == "__main__":
    main()
