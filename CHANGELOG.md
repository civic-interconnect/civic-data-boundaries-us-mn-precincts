# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format follows **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

### Added

- Added the generated `2026-05` Minnesota precinct snapshot derived from the Minnesota Secretary of State statewide GeoJSON source.

### Changed

- Updated precinct validation to preserve multiple source features that share a precinct identifier when their normalized precinct attributes are consistent.
- Updated the Minnesota precinct index to identify `2026-05` as the latest published snapshot.

### Fixed

- Changed generated index paths to use portable forward-slash paths instead of Windows path separators.

---

## [0.1.1] - 2026-09-28

### Added

- Added citation metadata and Zenodo archiving support.
- Added initial PyPI publishing through GitHub Actions Trusted Publishing.

---

## [0.1.0] - 2026-09-27

### Added

- Added `civic-us-mn refresh` to refresh Minnesota precinct data from the official statewide source.
- Added automatic derivation of `snapshot_date` and `snapshot_version` from source metadata.
- Added automated download, build, validation, and index generation for the current precinct snapshot.
- Added validation of the complete normalized precinct field contract.

### Changed

- Updated the project baseline to Python 3.14.
- Migrated the package build backend from setuptools to Hatchling.
- Migrated Git-tag-derived versioning from `setuptools_scm` to `hatch-vcs`.
- Updated dependency management to use PEP 735 dependency groups.
- Replaced Pyright with `ty` for type checking.
- Replaced the pre-commit runner with `prek`.
- Updated Ruff, pytest, and repository validation configuration.
- Updated continuous integration to the current Python and Zensical workflow.
- Updated precinct source configuration to use the current Minnesota Secretary of State statewide GeoJSON source.
- Changed downloaded source files under `data-in/` to local reproducible inputs rather than committed repository artifacts.
- Updated generated snapshot metadata to record the derived snapshot version and source date.

### Removed

- Removed obsolete setuptools and `setuptools_scm` configuration.
- Removed obsolete Pyright configuration.
- Removed legacy CI configuration superseded by the current workflow.

---

## [0.0.1] - 2025-10-29

### Added

- **Initial release**

---

## Notes on versioning and releases

- **SemVer policy**
  - **MAJOR** - breaking API/schema or CLI changes.
  - **MINOR** - backward-compatible additions and enhancements.
  - **PATCH** - documentation, tooling, or non-breaking fixes.
    Tag the repository with `vX.Y.Z` to publish a release.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### One-Time Zenodo Authorization

1. Sign in to Zenodo.
2. Open your profile menu in the upper-right.
3. Select My account / Settings / GitHub.
4. In GitHub Repositories / Click **Sync now**.
5. Find this organization / this repo.
6. Turn on the repository toggle/slider.
7. Refresh the page and confirm it appears as enabled.
8. Zenodo will ingest future GitHub Releases from this repo.

### Task 1. Update release metadata (manual edits)

1.1. CHANGELOG.md: add section, move unreleased entries, update links
1.2. CITATION.cff: update version and date-released (version appears twice)

### Task 2. Refresh Data, Update, and Validate

Run:

```powershell
# fetch new data
civic-us-mn refresh
civic-us-mn validate --version 2026-05
civic-us-mn index

# update
.\sit.ps1

# Update GitHub Actions and pin all action references to immutable SHAs
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Update hooks
uvx prek update
git add -A
uvx prek run --all-files

# Audit the resulting GitHub configuration for security findings
uvx zizmor@latest .github/

# Validate citation metadata
uvx cffconvert --validate

# Format markdown
npx markdownlint-cli2 --fix

# Clean generated (optional)
Get-ChildItem -Path . -Recurse -Directory -Filter "*__pycache__*" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Directory -Filter ".*_cache"  | Remove-Item -Recurse -Force
Get-ChildItem -Path "src" -Recurse -Directory -Name "*.egg-info" | Remove-Item -Recurse -Force
Remove-Item -Path "build", "dist", "site" -Recurse -Force

# Build and inspect the package
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
uv build
Get-ChildItem dist
$WHEEL = Get-ChildItem dist\*.whl | Select-Object -First 1
uv run python -m zipfile -l $WHEEL.FullName
```

### Task 3. Commit and Push

```shell
git add -A
git commit -m "Prep X.Y.Z"
git push -u origin main
```

Verify that all required GitHub Actions complete successfully.

### Task 4. Tag and Push the Release

After the required GitHub Actions succeed:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

Create GitHub Release after setting up Zenodo and pushing a tag,
for example with a command like this:

```shell
gh release create v0.1.1 --verify-tag --title "0.1.1"  --generate-notes
```

Then:

1. Confirm the GitHub Release was created successfully.
2. In Zenodo, confirm the GitHub release was ingested and archived.
3. Open the resulting Zenodo record and verify its metadata and DOI.

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/releases/tag/v0.1.1
[0.1.0]: https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/releases/tag/v0.1.0
[0.0.1]: https://github.com/civic-interconnect/civic-data-boundaries-us-mn-precincts/releases/tag/v0.0.1

<!-- markdownlint-enable MD024 -->
