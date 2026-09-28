# civic-data-boundaries-us-mn-precincts

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23006553.svg)](https://zenodo.org/records/23006553)
[![PyPI](https://img.shields.io/pypi/v/civic-data-boundaries-us-mn-precincts.svg)](https://pypi.org/project/civic-data-boundaries-us-mn-precincts/)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/actions/workflows/ci-python-zensical.yml/badge.svg)](https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/actions/workflows/ci-python-zensical.yml)
[![Docs](https://img.shields.io/badge/docs-Zensical-blue)](https://civic-interconnect.github.io/civic-data-boundaries-us-mn-precincts/)

> Civic Boundary Data for [Civic Interconnect](https://github.com/civic-interconnect) for Minnesota precincts.

## Source

- <https://www.sos.mn.gov/election-administration-campaigns/data-maps/geojson-files/>

## GeoJSON files

GeoJSON is a geospatial data format based on JSON (JavaScript Object Notation) designed for use in online applications. They include voting precinct boundaries as well as the name, county, and election districts (US Congress, MN Senate and House, County Commissioner) for each precinct.

These files are intended to provide basic information regarding the location of election districts within the state. For the most accurate information on precincts and districts, as well as polling place information, please use the [Polling Place Finder](https://www.sos.mn.gov/elections-voting/election-day-voting/where-do-i-vote/).

## Current Snapshot

The current statewide source reports:

- Source date: `2026-05-01`
- Snapshot version: `2026-05`
- Source: Minnesota Secretary of State statewide precinct GeoJSON

Snapshot version and date are derived automatically from the source metadata.

For state and county boundaries, see [civic-data-boundaries-us](https://github.com/civic-interconnect/civic-data-boundaries-us/).

## Process

```text
Official source:
https://www.sos.mn.gov/media/2791/mn-precincts.json

        ↓

Read top-level source date:
"May 1,2026"

        ↓

Normalize:
snapshot_date = "2026-05-01"

        ↓

Derive:
snapshot_version = "2026-05"

        ↓

Save downloaded input:
data-in/states/minnesota/precincts_2026-05.json

        ↓

Build output:
data-out/states/minnesota/precincts/2026-05/

        ↓

Add to every output feature:
snapshot_version = "2026-05"
snapshot_date = "2026-05-01"
```

## Installation

```shell
uv add civic-data-boundaries-us-mn-precincts
```

or with `pip`:

```shell
pip install civic-data-boundaries-us-mn-precincts
```

The command-line interface is installed as:

```shell
civic-us-mn --help
```

## Usage

Refresh the current Minnesota precinct snapshot from the official statewide source:

```shell
civic-us-mn refresh
```

The refresh command:

1. Downloads the current statewide GeoJSON from the Minnesota Secretary of State.
2. Reads and normalizes the source date.
3. Derives the snapshot version from the source date.
4. Writes the downloaded source under `data-in/`.
5. Builds normalized GeoJSON under `data-out/`.
6. Validates the generated snapshot.
7. Regenerates the dataset indexes.

Downloaded source files under `data-in/` are reproducible local inputs and are not committed.

Generated publication artifacts under `data-out/` are committed.

### Additional Commands

Validate a generated snapshot:

```shell
civic-us-mn validate --version 2026-05
```

Regenerate dataset indexes:

```shell
civic-us-mn index
```

Build from an already downloaded source file:

```shell
civic-us-mn build --version 2026-05
```

## Development

### Clone and Open in VS Code

```shell
git clone https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts.git
cd civic-data-boundaries-us-mn-precincts
code .
```

### Set Up the Project

```shell
uvx pup-clean --delete
uv self update
uv python pin 3.14
uv python install
uv lock --upgrade
uv sync
uv audit
```

## References

[State of Minnesota - Election Administration & Campaigns - Data & Maps - GeoJSON files](https://www.sos.mn.gov/election-administration-campaigns/data-maps/geojson-files/)

## Citation

[CITATION.cff](./CITATION.cff)

## License

[MIT](./LICENSE)
