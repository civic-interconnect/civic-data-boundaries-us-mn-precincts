# civic-data-boundaries-us-mn-precincts

[![PyPI](https://img.shields.io/pypi/v/civic-data-boundaries-us-mn-precincts.svg)](https://pypi.org/project/civic-data-boundaries-us-mn-precincts/)
[![Python versions](https://img.shields.io/pypi/pyversions/civic-data-boundaries-us-mn-precincts.svg)](https://pypi.org/project/civic-data-boundaries-us-mn-precincts/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/actions/workflows/ci.yml/badge.svg)](https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://civic-interconnect.github.io/civic-data-boundaries-us-mn-precincts/)

> Civic Boundary Data for [Civic Interconnect](https://github.com/civic-interconnect) for Minnesota precincts.

# Source

- <https://www.sos.mn.gov/election-administration-campaigns/data-maps/geojson-files/>

# GeoJSON files
GeoJSON is a geospatial data format based on JSON (JavaScript Object Notation) designed for use in online applications. They include voting precinct boundaries as well as the name, county, and election districts (US Congress, MN Senate and House, County Commissioner) for each precinct.

These files are intended to provide basic information regarding the location of election districts within the state. For the most accurate information on precincts and districts, as well as polling place information, please use the [Polling Place Finder](https://www.sos.mn.gov/elections-voting/election-day-voting/where-do-i-vote/).

# Minnesota precincts  - April 2025 (6225 KB json)

|Congressional District	| as of April 2025|
|-----------------------|-----------------|
|District 1 (southern Minnesota)	|C.D. 1 (1062 KB json)|
|District 2 (south Metro)	|C.D. 2 (383 KB json)|
|District 3 (greater Hennepin County)	|C.D. 3 (341 KB json)|
|District 4 (Ramsey County and suburbs)|	C.D. 4 (217 KB json)|
|District 5 (Minneapolis and suburbs)	|C.D. 5 (171 KB json)|
|District 6 (northwestern Metro, St Cloud area)|	C.D. 6 (578 KB json)|
|District 7 (western Minnesota)	|C.D. 7 (1760 KB json)|
|District 8 (northeastern Minnesota)	|C.D. 8 (1720 KB json)|

For state and county boundaries, see [civic-data-boundaries-us](https://github.com/civic-interconnect/civic-data-boundaries-us/).

---

## Installation

```shell
pip install civic-data-boundaries-us-mn-precincts
```

## Pipeline

This repository uses a reproducible data pipeline built on the same conventions as other Civic Interconnect datasets (data-config/, data-in/, data-out/).

```shell
# Place statewide GeoJSON input
# data-in/states/minnesota/precincts_2025-04.json

# 1) Build (copy/normalize/add snapshot metadata)
civic-us-mn build --version 2025-04

# 2) Validate (CRS, required columns, geometry, basic uniqueness)
civic-us-mn validate --version 2025-04

# 3) Index (flat index, manifest, state layer pointers)
civic-us-mn index

```

Or use `uv`:

```shell
uv run python -m civic_data_boundaries_us_mn_precincts.build_layer --version 2025-04
uv run python -m civic_data_boundaries_us_mn_precincts.validate --version 2025-04
uv run python -m civic_data_boundaries_us_mn_precincts.index
```
---

## Development

See [DEVELOPER.md](./DEVELOPER.md)

## Pipeline



## References

[State of Minnesota - Election Administration & Campaigns - Data & Maps - GeoJSON files](https://www.sos.mn.gov/election-administration-campaigns/data-maps/geojson-files/)

