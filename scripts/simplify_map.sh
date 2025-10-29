#!/usr/bin/env bash
set -euo pipefail

SRC="data-in/states/minnesota/precincts_2025-04.geojson"
OUTDIR="data-out/states/minnesota/precincts/2025-04"

mkdir -p "$OUTDIR"

# Full (unaltered)
cp "$SRC" "$OUTDIR/mn-precincts-full.geojson"

# Simplified GeoJSON (10% retain)
mapshaper "$SRC" \
  -simplify 10% keep-shapes \
  -o format=geojson "$OUTDIR/mn-precincts-web.geojson"

# Simplified TopoJSON (best for web map)
mapshaper "$SRC" \
  -simplify 10% keep-shapes \
  -o format=topojson "$OUTDIR/mn-precincts-web.topojson"

# Optional summary CSV
mapshaper "$SRC" \
  -each 'county=county||"Unknown"' \
  -o id-field=precinct_id \
  -o format=csv "$OUTDIR/mn-precincts-summary.csv"

echo "Outputs written to $OUTDIR"
