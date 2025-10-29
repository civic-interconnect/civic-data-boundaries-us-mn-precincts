"""Build pipeline for MN precincts (GeoJSON-in -> processed data-out).

Reads top-level `build:` section from data-config/us_mn_precincts.yaml.

Expected YAML (see example below) defines:
  - version (e.g., "2025-04")
  - input_path (under data-in/)
  - fields_* options
  - write_topojson / simplify_pct (optional)

Outputs under:
  data-out/states/minnesota/precincts/<version>/
    mn-precincts-full.geojson
    mn-precincts-web.geojson
    metadata.json
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

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
    """Custom exception for build errors in the MN precincts pipeline."""

    pass


# -------------------------
# Config helpers
# -------------------------


def _find_cfg_path() -> Path:
    """Find data-config/us_mn_precincts.yaml.

    Search order:
      1) ENV CIVIC_MN_CFG if set
      2) data-in/ upward
      3) this file's directory upward.
    """
    env_override = os.getenv("CIVIC_MN_CFG")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p
        raise BuildError(f"Config override not found: {p}")

    roots = [get_data_in_dir(), Path(__file__).resolve()]
    for root in roots:
        for base in [root, *root.parents]:
            cand = base / "data-config" / "us_mn_precincts.yaml"
            if cand.exists():
                return cand
    raise BuildError("Could not locate data-config/us_mn_precincts.yaml from known roots")


def _load_build_cfg() -> dict[str, Any]:
    """Load the top-level `build:` dict from data-config/us_mn_precincts.yaml."""
    cfg_path = _find_cfg_path()
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg_any = yaml.safe_load(f) or {}
    if not isinstance(cfg_any, dict):
        raise BuildError("Config YAML did not parse to a dict")
    build = cfg_any.get("build")
    if not isinstance(build, dict):
        raise BuildError("Missing 'build' section in us_mn_precincts.yaml")
    return build


def _input_path(build_cfg: dict[str, Any]) -> Path:
    rel = build_cfg.get("input_path")
    if not rel:
        raise BuildError("build.input_path is required")
    p = get_data_in_dir() / rel
    if not p.exists():
        raise BuildError(f"Input not found: {p}")
    return p


def _out_dir(version: str) -> Path:
    p = get_data_out_dir() / "states" / "minnesota" / "precincts" / version
    p.mkdir(parents=True, exist_ok=True)
    return p


# -------------------------
# Transform helpers
# -------------------------


def _normalize_columns(df: gpd.GeoDataFrame, to_lower: bool, trim: bool) -> gpd.GeoDataFrame:
    cols = []
    for c in df.columns:
        nc = c
        if to_lower:
            nc = nc.lower()
        if trim:
            nc = nc.strip()
        cols.append(nc)
    df.columns = cols
    return df


def _rename_columns(df: gpd.GeoDataFrame, mapping: dict[str, str]) -> gpd.GeoDataFrame:
    return df.rename(columns=mapping) if mapping else df


def _keep_columns(df: gpd.GeoDataFrame, keep: list[str]) -> gpd.GeoDataFrame:
    if not keep:
        return df
    cols = [c for c in keep if c in df.columns]
    if "geometry" not in cols:
        cols.append("geometry")
    return df[cols]


def _add_constant_fields(df: gpd.GeoDataFrame, add_fields: dict[str, Any]) -> gpd.GeoDataFrame:
    for k, v in (add_fields or {}).items():
        df[k] = v
    return df


# -------------------------
# TopoJSON
# -------------------------


def _which_mapshaper() -> Path | None:
    exe = shutil.which("mapshaper")
    if not exe:
        return None
    p = Path(exe)
    return p if p.exists() and p.is_file() else None


def _clamped_pct(val: Any, lo: int = 0, hi: int = 50) -> int:
    try:
        v = int(val)
    except Exception:
        v = 0
    return max(lo, min(hi, v))


def _repair_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Try make_valid on invalid rows only
    invalid_mask = ~gdf.geometry.is_valid
    if invalid_mask.any():
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].map(make_valid)

    # Fallback: buffer(0) for any remaining invalids (handles self-intersections)
    invalid_mask = ~gdf.geometry.is_valid
    if invalid_mask.any():
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

    # Normalize to Polygon/MultiPolygon to avoid mixed types
    def _to_multi(geom):
        if geom is None or geom.is_empty:
            return geom
        if isinstance(geom, Polygon):
            return MultiPolygon([geom])
        return geom

    gdf["geometry"] = gdf.geometry.map(_to_multi)

    # Drop empties if any got nuked during repair (rare but possible)
    return gdf[~gdf.geometry.is_empty]


def _write_topojson(
    mapshaper_exe: Path, web_geojson: Path, topo_path: Path, simplify_pct: int
) -> Path | None:
    args = [str(mapshaper_exe), str(web_geojson)]
    pct = _clamped_pct(simplify_pct)
    if pct > 0:
        args += ["-simplify", f"{pct}%", "keep-shapes"]
    args += ["-o", "format=topojson", str(topo_path)]

    # Safe: no shell, executable discovered via PATH, arguments are constructed (not user-supplied)
    res = subprocess.run(args, capture_output=True, text=True)  # noqa: S603
    if res.returncode != 0:
        logger.warning(f"mapshaper failed; stdout={res.stdout} stderr={res.stderr}")
        return None

    logger.info(f"Wrote TopoJSON: {topo_path}")
    return topo_path


# -------------------------
# Metadata
# -------------------------


def _write_metadata(full_path: Path, web_name: str, topo_name: str | None, out_dir: Path) -> Path:
    gdf = gpd.read_file(full_path)
    minx, miny, maxx, maxy = [float(x) for x in gdf.total_bounds]
    meta = {
        "id": "mn-precincts",
        "title": "Minnesota Precincts",
        "paths": {
            "full_geojson": "mn-precincts-full.geojson",
            "web_geojson": web_name,
            "web_topojson": topo_name,
        },
        "stats": {
            "features": int(len(gdf)),
            "bbox": [round(minx, 6), round(miny, 6), round(maxx, 6), round(maxy, 6)],
        },
        "spatial": {"crs": "EPSG:4326", "geometry_type": "Polygon"},
    }
    mp = out_dir / "metadata.json"
    with mp.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Wrote metadata: {mp}")
    return mp


# -------------------------
# Main
# -------------------------


def main(version: str | None = None) -> int:
    """Build the MN precincts data layer by processing GeoJSON input and writing output files.

    Parameters
    ----------
    version : str | None
        Snapshot tag/version for output directory naming.

    Returns
    -------
    int
        0 if build succeeded, 1 if an error occurred.
    """
    try:
        build_cfg = _load_build_cfg()
        version = version or build_cfg.get("version")
        if not version:
            raise BuildError("build.version is required")

        src_path = _input_path(build_cfg)
        out_dir = _out_dir(version)

        gdf: gpd.GeoDataFrame = gpd.read_file(src_path)

        gdf = _normalize_columns(
            gdf,
            to_lower=bool(build_cfg.get("fields_lowercase", True)),
            trim=bool(build_cfg.get("fields_trim", True)),
        )
        gdf = _rename_columns(gdf, mapping=build_cfg.get("fields_rename") or {})
        gdf = _add_constant_fields(gdf, add_fields=build_cfg.get("add_fields") or {})
        gdf = _keep_columns(gdf, keep=build_cfg.get("fields_keep") or [])
        gdf = _repair_geometries(gdf)

        full_path = out_dir / "mn-precincts-full.geojson"
        gdf.to_file(full_path, driver="GeoJSON")
        logger.info(f"Wrote full: {full_path}")

        web_geojson_name = "mn-precincts-web.geojson"
        web_geojson_path = out_dir / web_geojson_name
        shutil.copy2(full_path, web_geojson_path)
        logger.info(f"Wrote web geojson: {web_geojson_path}")

        topo_name: str | None = None
        if bool(build_cfg.get("write_topojson", False)):
            exe = _which_mapshaper()
            if exe:
                topo_path = out_dir / "mn-precincts-web.topojson"
                topo_out = _write_topojson(
                    exe,
                    web_geojson_path,
                    topo_path,
                    simplify_pct=_clamped_pct(build_cfg.get("simplify_pct", 0)),
                )
                topo_name = topo_out.name if topo_out else None
            else:
                logger.warning("mapshaper not found; skipping TopoJSON.")

        _write_metadata(
            full_path=full_path,
            web_name=web_geojson_name,
            topo_name=topo_name,
            out_dir=out_dir,
        )

        logger.info("Build completed.")
        return 0

    except Exception as exc:
        logger.error(f"Build failed: {exc}")
        return 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Build MN precincts (GeoJSON processing).")
    ap.add_argument("--version", "-v", help="Snapshot tag like 2025-04")
    args = ap.parse_args()
    raise SystemExit(main(version=args.version))
