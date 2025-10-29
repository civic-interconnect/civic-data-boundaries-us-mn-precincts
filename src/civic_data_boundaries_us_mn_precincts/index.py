"""Generates index files and summary metadata in data-out/.

- data-out/index.json: flat listing of all GeoJSONs with bbox and feature counts
- data-out/states/minnesota/index.json: layer pointers to latest versions
- data-out/states/minnesota/precincts/<version>/metadata.json: written by build

CLI:
  uv run python -m civic_data_boundaries_us_mn_precincts.index
"""

import json
from pathlib import Path
from typing import Any

from civic_lib_core import date_utils, log_utils
import geopandas as gpd

from civic_data_boundaries_us_mn_precincts.utils.get_paths import get_data_out_dir

logger = log_utils.logger


class IndexBuildError(Exception):
    """Custom exception for errors encountered during index building."""

    pass


def _compute_bbox(geojson_path: Path) -> list[float] | None:
    try:
        gdf: gpd.GeoDataFrame = gpd.read_file(geojson_path)
        minx, miny, maxx, maxy = [float(x) for x in gdf.total_bounds]
        return [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)]
    except Exception as e:
        logger.warning(f"Could not read {geojson_path.name}: {e}")
        return None


def _compute_feature_count(geojson_path: Path) -> int | None:
    try:
        gdf: gpd.GeoDataFrame = gpd.read_file(geojson_path)
        return int(len(gdf))
    except Exception as e:
        logger.warning(f"Could not count features in {geojson_path.name}: {e}")
        return None


def _write_manifest(out_dir: Path, index_data: list[dict[str, Any]]) -> Path:
    total_files = len(index_data)
    total_features = sum(d.get("features", 0) for d in index_data)

    manifest: dict[str, Any] = {
        "dataset": "mn-precincts",
        "description": "Minnesota precinct boundaries",
        "source": "Minnesota Secretary of State",
        "license": "Public domain",
        "geometry_type": "Polygon",
        "generated_at": date_utils.now_utc_str(),
        "total_files": total_files,
        "total_features": total_features,
        "files_indexed": [d["path"] for d in index_data],
    }
    p = out_dir / "manifest.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written: {p}")
    return p


def _latest_version_in(out_root: Path) -> str | None:
    """Return the latest version folder name under data-out/states/minnesota/precincts/<version>/.

    Uses simple descending sort.
    """
    base = out_root / "states" / "minnesota" / "precincts"
    if not base.exists():
        return None
    versions = sorted([p.name for p in base.iterdir() if p.is_dir()], reverse=True)
    return versions[0] if versions else None


def _write_state_index(out_root: Path) -> Path | None:
    """Generate and write a state index JSON file for Minnesota precincts.

    The function determines the latest versioned precinct folder within the specified output root directory.
    If a version is found, it creates a state index JSON file referencing the latest precinct metadata and writes it to
    'states/minnesota/index.json' under the output root. If no versioned folder is found, it logs a warning and returns None.

    Args:
        out_root (Path): The root directory where precinct data is stored.

    Returns:
        Path | None: The path to the written state index JSON file, or None if no versioned precinct folder is found.
    """
    latest = _latest_version_in(out_root)
    if not latest:
        logger.warning("No versioned precinct folder found. Skipping state index.")
        return None

    state_index = {
        "layers": [{"id": "mn-precincts", "latest": f"precincts/{latest}/metadata.json"}]
    }
    p = out_root / "states" / "minnesota" / "index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(state_index, f, indent=2)
    logger.info(f"State index written: {p}")
    return p


def build_index_main() -> int:
    """Scan data-out for GeoJSON, compute metadata, generate index and manifest.

    Workflow:
    1. Scans the output directory for all GeoJSON files.
    2. For each file, computes its bounding box and feature count.
    3. Writes a flat index of all files to 'index.json'.
    4. Writes a dataset-level manifest to 'manifest.json'.
    5. Writes a state-level index to 'states/minnesota/index.json'.

    Returns:
        int: 0 if the index build succeeds, 1 if an error occurs.
    """
    try:
        out_root = get_data_out_dir()
        flat_index: list[dict[str, Any]] = []

        logger.info(f"Scanning {out_root} for GeoJSONs...")
        for geojson in out_root.rglob("*.geojson"):
            bbox = _compute_bbox(geojson)
            nfeat = _compute_feature_count(geojson)
            flat_index.append(
                {
                    "path": str(geojson.relative_to(out_root)),
                    "bbox": bbox,
                    "features": nfeat,
                }
            )

        # data-out/index.json
        index_file = out_root / "index.json"
        with index_file.open("w", encoding="utf-8") as f:
            json.dump(flat_index, f, indent=2)
        logger.info(f"Flat index written: {index_file} ({len(flat_index)} files)")

        # data-out/manifest.json (dataset-level)
        _write_manifest(out_root, flat_index)

        # data-out/states/minnesota/index.json (layer pointers)
        _write_state_index(out_root)

        return 0

    except Exception as e:
        logger.error(f"Index build failed: {e}")
        return 1


def main() -> int:
    """Execute the main entry point for building the index.

    Returns:
        int: 0 if the index was built successfully, 1 if an unexpected error occurred.
    """
    try:
        return build_index_main()
    except Exception as e:
        logger.error(f"Index command failed unexpectedly: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
