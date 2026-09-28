"""Build pipeline for Minnesota precincts.

Reads transformation configuration from the packaged
data/us_mn_precincts.yaml resource.

Snapshot version, source date, and input path are supplied dynamically
by the refresh workflow.

Outputs under:
  data-out/states/minnesota/precincts/<version>/
    mn-precincts-full.geojson
    mn-precincts-web.geojson
    metadata.json
"""

from importlib.resources import files
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, cast

from civic_lib_core import log_utils
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from shapely.validation import make_valid
import yaml

from civic_data_boundaries_us_mn_precincts.utils.get_paths import (
    get_data_in_dir,
    get_data_out_dir,
)

logger = log_utils.logger


class BuildError(RuntimeError):
    """Custom exception for build errors in the Minnesota precincts pipeline."""


# -------------------------
# Config helpers
# -------------------------


def _load_build_cfg() -> dict[str, Any]:
    """Load the packaged build configuration."""
    config_text = (
        files("civic_data_boundaries_us_mn_precincts")
        .joinpath("data", "us_mn_precincts.yaml")
        .read_text(encoding="utf-8")
    )

    config = yaml.safe_load(config_text) or {}

    if not isinstance(config, dict):
        raise BuildError("Config YAML did not parse to a dict")

    build = config.get("build")

    if not isinstance(build, dict):
        raise BuildError("Missing 'build' section in us_mn_precincts.yaml")

    return build


def _out_dir(version: str) -> Path:
    """Return and create the output directory for a snapshot version."""
    path = get_data_out_dir() / "states" / "minnesota" / "precincts" / version
    path.mkdir(parents=True, exist_ok=True)
    return path


# -------------------------
# Transform helpers
# -------------------------


def _normalize_columns(
    df: gpd.GeoDataFrame,
    to_lower: bool,
    trim: bool,
) -> gpd.GeoDataFrame:
    """Normalize source column names."""
    columns = []

    for column in df.columns:
        normalized = column

        if to_lower:
            normalized = normalized.lower()

        if trim:
            normalized = normalized.strip()

        columns.append(normalized)

    df.columns = columns
    return df


def _rename_columns(
    df: gpd.GeoDataFrame,
    mapping: dict[str, str],
) -> gpd.GeoDataFrame:
    """Rename columns while preserving GeoDataFrame typing."""
    if not mapping:
        return df

    renamed = df.rename(columns=mapping)
    return cast("gpd.GeoDataFrame", renamed)


def _keep_columns(
    df: gpd.GeoDataFrame,
    keep: list[str],
) -> gpd.GeoDataFrame:
    """Keep configured columns while preserving geometry and CRS."""
    if not keep:
        return df

    columns = [column for column in keep if column in df.columns]

    if "geometry" not in columns:
        columns.append("geometry")

    return gpd.GeoDataFrame(
        df.loc[:, columns],
        geometry="geometry",
        crs=df.crs,
    )


def _add_constant_fields(
    df: gpd.GeoDataFrame,
    add_fields: dict[str, Any],
) -> gpd.GeoDataFrame:
    """Add constant metadata fields."""
    for key, value in add_fields.items():
        df[key] = value

    return df


# -------------------------
# TopoJSON
# -------------------------


def _which_mapshaper() -> Path | None:
    """Return the mapshaper executable when available."""
    executable = shutil.which("mapshaper")

    if not executable:
        return None

    path = Path(executable)
    return path if path.exists() and path.is_file() else None


def _clamped_pct(
    value: Any,
    lo: int = 0,
    hi: int = 50,
) -> int:
    """Convert and clamp a simplification percentage."""
    try:
        result = int(value)
    except TypeError, ValueError:
        result = 0

    return max(lo, min(hi, result))


def _repair_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Repair invalid geometries and normalize polygons."""
    invalid_mask = ~gdf.geometry.is_valid

    if invalid_mask.any():
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].map(
            make_valid
        )

    invalid_mask = ~gdf.geometry.is_valid

    if invalid_mask.any():
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

    def _to_multi(geometry):
        if geometry is None or geometry.is_empty:
            return geometry

        if isinstance(geometry, Polygon):
            return MultiPolygon([geometry])

        return geometry

    gdf["geometry"] = gdf.geometry.map(_to_multi)

    return gdf[~gdf.geometry.is_empty]


def _write_topojson(
    mapshaper_exe: Path,
    web_geojson: Path,
    topo_path: Path,
    simplify_pct: int,
) -> Path | None:
    """Write optional TopoJSON output using mapshaper."""
    args = [str(mapshaper_exe), str(web_geojson)]

    pct = _clamped_pct(simplify_pct)

    if pct > 0:
        args += ["-simplify", f"{pct}%", "keep-shapes"]

    args += ["-o", "format=topojson", str(topo_path)]

    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.warning(
            f"mapshaper failed; stdout={result.stdout} stderr={result.stderr}"
        )
        return None

    logger.info(f"Wrote TopoJSON: {topo_path}")
    return topo_path


# -------------------------
# Metadata
# -------------------------


def _write_metadata(
    full_path: Path,
    web_name: str,
    topo_name: str | None,
    out_dir: Path,
    version: str,
    snapshot_date: str | None,
) -> Path:
    """Write metadata for a generated snapshot."""
    gdf = gpd.read_file(full_path)

    minx, miny, maxx, maxy = [float(value) for value in gdf.total_bounds]

    metadata = {
        "id": "mn-precincts",
        "title": "Minnesota Precincts",
        "paths": {
            "full_geojson": "mn-precincts-full.geojson",
            "web_geojson": web_name,
            "web_topojson": topo_name,
        },
        "stats": {
            "features": len(gdf),
            "bbox": [
                round(minx, 6),
                round(miny, 6),
                round(maxx, 6),
                round(maxy, 6),
            ],
        },
        "spatial": {
            "crs": "EPSG:4326",
            "geometry_type": "Polygon",
        },
        "snapshot_version": version,
        "snapshot_date": snapshot_date,
    }

    metadata_path = out_dir / "metadata.json"

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    logger.info(f"Wrote metadata: {metadata_path}")
    return metadata_path


# -------------------------
# Main
# -------------------------


def main(
    version: str | None = None,
    input_path: Path | None = None,
    snapshot_date: str | None = None,
) -> int:
    """Build the Minnesota precinct layer.

    Args:
        version: Snapshot version used for output directory naming.
        input_path: Optional explicit source GeoJSON path.
        snapshot_date: Source snapshot date in YYYY-MM-DD format.

    Returns:
        0 when the build succeeds; otherwise 1.
    """
    try:
        build_cfg = _load_build_cfg()

        if not version:
            raise BuildError("version is required")

        if input_path is not None:
            source_path = input_path
        else:
            source_path = (
                get_data_in_dir() / "states" / "minnesota" / f"precincts_{version}.json"
            )

        if not source_path.exists():
            raise BuildError(f"Input not found: {source_path}")

        out_dir = _out_dir(version)

        gdf: gpd.GeoDataFrame = gpd.read_file(source_path)

        gdf = _normalize_columns(
            gdf,
            to_lower=bool(build_cfg.get("fields_lowercase", True)),
            trim=bool(build_cfg.get("fields_trim", True)),
        )

        gdf = _rename_columns(
            gdf,
            mapping=build_cfg.get("fields_rename") or {},
        )

        add_fields: dict[str, Any] = {
            "snapshot_version": version,
        }

        if snapshot_date is not None:
            add_fields["snapshot_date"] = snapshot_date

        gdf = _add_constant_fields(
            gdf,
            add_fields=add_fields,
        )

        gdf = _keep_columns(
            gdf,
            keep=build_cfg.get("fields_keep") or [],
        )

        if bool(build_cfg.get("repair_geometries", True)):
            gdf = _repair_geometries(gdf)

        full_path = out_dir / "mn-precincts-full.geojson"

        gdf.to_file(
            full_path,
            driver="GeoJSON",
        )

        logger.info(f"Wrote full: {full_path}")

        web_geojson_name = "mn-precincts-web.geojson"
        web_geojson_path = out_dir / web_geojson_name

        shutil.copy2(
            full_path,
            web_geojson_path,
        )

        logger.info(f"Wrote web GeoJSON: {web_geojson_path}")

        topo_name: str | None = None

        if bool(build_cfg.get("write_topojson", False)):
            executable = _which_mapshaper()

            if executable:
                topo_path = out_dir / "mn-precincts-web.topojson"

                topo_output = _write_topojson(
                    executable,
                    web_geojson_path,
                    topo_path,
                    simplify_pct=_clamped_pct(build_cfg.get("simplify_pct", 0)),
                )

                topo_name = topo_output.name if topo_output else None
            else:
                logger.warning("mapshaper not found; skipping TopoJSON.")

        _write_metadata(
            full_path=full_path,
            web_name=web_geojson_name,
            topo_name=topo_name,
            out_dir=out_dir,
            version=version,
            snapshot_date=snapshot_date,
        )

        logger.info("Build completed.")
        return 0

    except BuildError as exc:
        logger.error(f"Build failed: {exc}")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Minnesota precincts from GeoJSON input."
    )
    parser.add_argument(
        "--version",
        "-v",
        required=True,
        help="Snapshot version such as 2026-05",
    )

    arguments = parser.parse_args()

    raise SystemExit(main(version=arguments.version))
