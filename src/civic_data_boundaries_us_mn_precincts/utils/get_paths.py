"""civic_data_boundaries_us_mn_precincts.utils.get_paths.

Utilities for resolving paths to various data directories
in the civic_data_boundaries_us_mn_precincts package.
"""

from pathlib import Path

__all__ = [
    "get_repo_root",
    "get_data_in_dir",
    "get_data_out_dir",
    "get_tiger_in_dir",
    "get_states_out_dir",
    "get_national_out_dir",
    "get_cd118_in_dir",
    "get_cd118_out_dir",
]


def get_repo_root(levels_up: int = 3) -> Path:
    """Return the root directory of this repo by walking up a fixed number of parent folders.

    Defaults to 3 levels up, assuming this file is under:
        src/civic_data_boundaries_us/utils/
    """
    return Path(__file__).resolve().parents[levels_up]


# ---------- DATA-IN ----------


def get_data_in_dir() -> Path:
    """Return the root data-in directory for raw input data (downloads, archives)."""
    return get_repo_root() / "data-in"


def get_tiger_in_dir() -> Path:
    """Return the folder under data-in/ where TIGER shapefiles are stored after download and extraction."""
    return get_data_in_dir() / "tiger"


def get_cd118_in_dir() -> Path:
    """Return the folder under data-in/ where raw CD118 shapefiles are extracted."""
    return get_tiger_in_dir() / "tl_2022_us_cd118"


# ---------- DATA-OUT ----------


def get_data_out_dir() -> Path:
    """Return the root data-out directory for processed GeoJSON and chunked outputs."""
    return get_repo_root() / "data-out"


def get_states_out_dir() -> Path:
    """Return the directory under data-out/ where per-state folders are written."""
    return get_data_out_dir() / "states"


def get_national_out_dir() -> Path:
    """Return the directory under data-out/ where national-level files are written.

    Includes layers like national states, counties, or CD118 merged geojsons.
    """
    return get_data_out_dir() / "national"


def get_cd118_out_dir() -> Path:
    """Return the directory under data-out/national/ where CD118 geojsons are stored."""
    return get_national_out_dir()
