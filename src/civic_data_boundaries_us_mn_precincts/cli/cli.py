"""CLI for MN precincts workflow (GeoJSON-in -> data-out).

Commands:
  civic-us-mn build --version 2025-04
  civic-us-mn validate --version 2025-04
  civic-us-mn index
"""

import sys

from civic_lib_core import log_utils
import typer

from civic_data_boundaries_us_mn_precincts import build_layer, validate
from civic_data_boundaries_us_mn_precincts import index as index_mod

logger = log_utils.logger
app = typer.Typer(add_completion=False, help="MN Precincts CLI")


@app.command("build")
def cmd_build(
    version: str = typer.Option(..., "--version", "-v", help="Snapshot tag like 2025-04"),
) -> None:
    """Build the MN precincts layer for a given snapshot version.

    Parameters
    ----------
    version : str
        Snapshot tag like '2025-04'.
    """
    code = build_layer.main(version=version)
    raise typer.Exit(code)


@app.command("validate")
def cmd_validate(
    version: str = typer.Option(..., "--version", "-v", help="Snapshot tag like 2025-04"),
) -> None:
    """Validate the MN precincts layer for a given snapshot version.

    Parameters
    ----------
    version : str
        Snapshot tag like '2025-04'.
    """
    code = validate.main(version=version)
    raise typer.Exit(code)


@app.command("index")
def cmd_index() -> None:
    """Run the index command to build the MN precincts index."""
    code = index_mod.main()
    raise typer.Exit(code)


def main() -> int:
    """Entry point for the MN Precincts CLI.

    Runs the Typer app and handles exceptions, returning an appropriate exit code.
    """
    try:
        app()
        return 0
    except Exception as exc:
        logger.error(f"CLI error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
