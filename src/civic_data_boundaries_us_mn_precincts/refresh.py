"""Refresh Minnesota precinct data from the official statewide source."""

from datetime import UTC, datetime
from importlib.resources import files
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from civic_lib_core import log_utils
import yaml

from civic_data_boundaries_us_mn_precincts import build_layer, validate
from civic_data_boundaries_us_mn_precincts import index as index_mod
from civic_data_boundaries_us_mn_precincts.utils.get_paths import (
    get_data_in_dir,
    get_data_out_dir,
)

logger = log_utils.logger


class RefreshError(RuntimeError):
    """Raised when the Minnesota precinct refresh cannot be completed."""


def _load_source_url() -> str:
    """Load the official statewide source URL from packaged configuration."""
    config_text = (
        files("civic_data_boundaries_us_mn_precincts")
        .joinpath("data", "us_mn_precincts.yaml")
        .read_text(encoding="utf-8")
    )
    config = yaml.safe_load(config_text) or {}

    try:
        return str(config["layers"]["mn_precincts_statewide"]["url"])
    except (KeyError, TypeError) as exc:
        raise RefreshError("Missing Minnesota statewide source URL") from exc


def _parse_source_date(value: str) -> str:
    """Normalize the source date to ISO 8601 YYYY-MM-DD format."""
    normalized = " ".join(value.replace(",", ", ").split())

    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return (
                datetime.strptime(normalized, fmt)
                .replace(tzinfo=UTC)
                .date()
                .isoformat()
            )
        except ValueError:
            continue

    raise RefreshError(f"Unsupported source date: {value!r}")


def _read_source_metadata(data: bytes) -> tuple[str, str]:
    """Read the source date and derive the snapshot version."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise RefreshError("Downloaded Minnesota source is not valid JSON") from exc

    source_date_raw = payload.get("date")

    if not isinstance(source_date_raw, str) or not source_date_raw.strip():
        raise RefreshError("Minnesota source does not contain a top-level date")

    source_date = _parse_source_date(source_date_raw)
    version = source_date[:7]

    return source_date, version


def _already_current(version: str, source_date: str) -> bool:
    """Return whether the generated snapshot already matches the source date."""
    metadata_path = (
        get_data_out_dir()
        / "states"
        / "minnesota"
        / "precincts"
        / version
        / "metadata.json"
    )

    if not metadata_path.exists():
        return False

    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    return metadata.get("snapshot_date") == source_date


def _download(url: str) -> bytes:
    """Download the official statewide precinct source."""
    request = Request(
        url,
        headers={"User-Agent": "civic-interconnect-mn-precincts/1"},
    )

    with urlopen(request, timeout=120) as response:
        return response.read()


def main() -> int:
    """Download, build, validate, and index the current Minnesota precinct snapshot."""
    try:
        source_url = _load_source_url()

        logger.info(f"Fetching Minnesota precinct source: {source_url}")
        data = _download(source_url)

        source_date, version = _read_source_metadata(data)

        logger.info(f"Source date: {source_date}")
        logger.info(f"Snapshot version: {version}")

        if _already_current(version, source_date):
            logger.info("Snapshot is already current.")
            return 0

        input_path = (
            get_data_in_dir() / "states" / "minnesota" / f"precincts_{version}.json"
        )
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_bytes(data)

        if (
            build_layer.main(
                version=version,
                input_path=input_path,
                snapshot_date=source_date,
            )
            != 0
        ):
            raise RefreshError("Build failed")

        if validate.main(version=version) != 0:
            raise RefreshError("Validation failed")

        if index_mod.main() != 0:
            raise RefreshError("Index generation failed")

        logger.info(f"Refresh completed successfully for {version}.")
        return 0

    except (RefreshError, OSError, URLError, ValueError, yaml.YAMLError) as exc:
        logger.error(f"Refresh failed: {exc}")
        return 1
