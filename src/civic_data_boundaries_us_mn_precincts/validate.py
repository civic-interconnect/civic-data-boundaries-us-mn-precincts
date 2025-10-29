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
)

REQUIRED_FILES: tuple[str, ...] = (
    "mn-precincts-full.geojson",
    "mn-precincts-web.geojson",
    "metadata.json",
)


class ValidateError(RuntimeError):
    """Custom error class for validation errors."""

    pass


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


def _check_precinct_id_unique(gdf: gpd.GeoDataFrame, col: str = "precinct_id") -> None:
    if col not in gdf.columns:
        return
    dups = gdf[col][gdf[col].duplicated()].unique()
    if len(dups) > 0:
        raise ValidateError(f"Duplicate {col} values: {list(dups)[:10]}...")


def main(version: str) -> int:
    """Validate MN precincts outputs for the specified snapshot version."""
    try:
        out_dir = _out_dir(version)
        _require_files(out_dir, REQUIRED_FILES)

        full_path = out_dir / "mn-precincts-full.geojson"
        gdf = _load_gdf(full_path)

        _require_columns(gdf, REQUIRED_COLUMNS)
        _check_precinct_id_unique(gdf, "precinct_id")

        logger.info("Validation passed.")
        return 0
    except Exception as exc:
        logger.error(f"Validation failed: {exc}")
        return 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate MN precincts outputs.")
    ap.add_argument("--version", "-v", required=True, help="Snapshot tag like 2025-04")
    args = ap.parse_args()
    raise SystemExit(main(version=args.version))
