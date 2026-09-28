"""Validate MN precincts outputs in data-out/.

Checks:
- required files exist for a given snapshot version
- GeoJSON loads; geometry not empty
- CRS is EPSG:4326 (WGS84 lon/lat)
- required columns present after build
- optional: precinct_id uniqueness if present

Usage:
  uv run python -m civic_data_boundaries_us_mn_precincts.validate --version 2025-04
"""

from collections.abc import Iterable
from pathlib import Path

from civic_lib_core import log_utils
import geopandas as gpd

from civic_data_boundaries_us_mn_precincts.utils.get_paths import get_data_out_dir

logger = log_utils.logger

REQUIRED_COLUMNS: tuple[str, ...] = (
    "precinct_id",
    "precinct_name",
    "county",
    "us_house",
    "mn_senate",
    "mn_house",
    "county_commission",
    "snapshot_version",
    "snapshot_date",
)

REQUIRED_FILES: tuple[str, ...] = (
    "mn-precincts-full.geojson",
    "mn-precincts-web.geojson",
    "metadata.json",
)


class ValidateError(RuntimeError):
    """Custom error class for validation errors."""


def _out_dir(version: str) -> Path:
    p = get_data_out_dir() / "states" / "minnesota" / "precincts" / version
    if not p.exists():
        raise ValidateError(f"Missing output folder: {p}")
    return p


def _require_files(folder: Path, names: Iterable[str]) -> None:
    missing = [n for n in names if not (folder / n).exists()]
    if missing:
        raise ValidateError(f"Missing output files: {missing}")


def _load_gdf(geojson_path: Path) -> gpd.GeoDataFrame:
    try:
        gdf = gpd.read_file(geojson_path)
    except Exception as exc:
        raise ValidateError(f"Failed to read {geojson_path}: {exc}") from exc
    if gdf.empty:
        raise ValidateError(f"No features in {geojson_path}")
    if gdf.crs is None or str(gdf.crs).lower() not in ("epsg:4326", "wgs84"):
        raise ValidateError(f"CRS must be EPSG:4326. Found: {gdf.crs}")
    if not gdf.geometry.is_valid.all():
        invalid = (~gdf.geometry.is_valid).sum()
        raise ValidateError(f"Found {invalid} invalid geometries in {geojson_path}")
    return gdf


def _require_columns(gdf: gpd.GeoDataFrame, cols: Iterable[str]) -> None:
    missing = [c for c in cols if c not in gdf.columns]
    if missing:
        raise ValidateError(f"Missing required columns: {missing}")


def _check_precinct_id_consistency(
    gdf: gpd.GeoDataFrame,
    col: str = "precinct_id",
) -> None:
    """Require duplicate precinct IDs to have consistent attributes."""
    if col not in gdf.columns:
        return

    duplicate_rows = gdf[gdf[col].duplicated(keep=False)]

    if duplicate_rows.empty:
        return

    compare_columns = [
        "precinct_name",
        "county",
        "us_house",
        "mn_senate",
        "mn_house",
        "county_commission",
        "snapshot_version",
        "snapshot_date",
    ]

    for precinct_id, group in duplicate_rows.groupby(col):
        for column in compare_columns:
            if group[column].nunique(dropna=False) > 1:
                raise ValidateError(
                    f"Conflicting values for {col} {precinct_id!r} in column {column!r}"
                )


def main(version: str) -> int:
    """Validate MN precincts outputs for the specified snapshot version."""
    try:
        out_dir = _out_dir(version)
        _require_files(out_dir, REQUIRED_FILES)

        full_path = out_dir / "mn-precincts-full.geojson"
        gdf = _load_gdf(full_path)

        _require_columns(gdf, REQUIRED_COLUMNS)
        _check_precinct_id_consistency(gdf, "precinct_id")

        logger.info("Validation passed.")
        return 0
    except ValidateError as exc:
        logger.error(f"Validation failed: {exc}")
        return 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate MN precincts outputs.")
    ap.add_argument("--version", "-v", required=True, help="Snapshot tag like 2025-04")
    args = ap.parse_args()
    raise SystemExit(main(version=args.version))
