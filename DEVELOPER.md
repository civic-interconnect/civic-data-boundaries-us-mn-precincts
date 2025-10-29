# DEVELOPER.md

## Prerequisites: Set Up Machine

- View hidden files and folders
- View file extensions
- Git
- VS Code (recommended)
- **[uv](https://github.com/astral-sh/uv)**

## Fork and Clone Repository

1. Fork the repo.
2. Clone your repo to your machine and open it in VS Code.

Open a terminal and run the following commands.

```shell
git clone https://github.com/YOUR_USERNAME/civic-data-boundaries-us-mn-precincts.git
cd civic-data-boundaries-us-mn-precincts
```

## Dev 1. One-time setup

- Open the repo directory in VS Code.
- Open a terminal in VS Code.

```shell
uv python pin 3.12
uv venv

.venv\Scripts\activate # Windows
# source .venv/bin/activate  # Mac/Linux/WSL

uv sync --extra dev --extra docs --upgrade
uv run pre-commit install
```

## Dev 2. Validate Local Changes

```shell
git pull origin main
uvx pre-commit autoupdate
git add .
uvx ruff check . --fix
uvx ruff format .
uvx deptry .
uvx pyright
uv run pytest
```

Run the pre-commit hooks (twice, if needed):

```shell
pre-commit run --all-files
```

## DEV 3. Regenerate (Optional) and Build and Inspect Package

```shell
uv run civic-us-cd118 fetch
uv run civic-us-cd118 export
uv run civic-us-cd118 index
uv run civic-us-cd118 cleanup
```

```shell
uv build

$TMP = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath()) -Name ("wheel_" + [System.Guid]::NewGuid())
Expand-Archive dist\*.whl -DestinationPath $TMP.FullName
Get-ChildItem -Recurse $TMP.FullName | ForEach-Object { $_.FullName.Replace($TMP.FullName + '\','') }
Remove-Item -Recurse -Force $TMP
```

## DEV 4. Build and Preview Docs

```shell
uv run mkdocs build --strict
uv run mkdocs serve
```

Verify local API docs at: <http://localhost:8000>
When done reviewing, use CTRL c or CMD c to quit.

## DEV 5. Clean Artifacts (Optional)

```shell
Get-ChildItem -Path . -Recurse -Directory -Filter "*__pycache__*" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Directory -Filter ".*_cache"  | Remove-Item -Recurse -Force
Get-ChildItem -Path "src" -Recurse -Directory -Name "*.egg-info" | Remove-Item -Recurse -Force
Remove-Item -Path "build", "dist", "site" -Recurse -Force
```

## DEV 6. Test

Update `CHANGELOG.md` and `pyproject`.toml dependencies.
Ensure CI passes.

```shell
uv run pre-commit run --all-files
uv run pytest -q
```

## DEV 7. Git add-commit-push Changes

```shell
git add .
git commit -m "Prep vx.y.z"
git push -u origin main
```

## DEV 8. Git tag and Push tag

**Important:** Wait for GitHub Actions from prior step to complete successfully (all green checks).
If any fail, fix issues and push again before tagging.

```shell
git tag vx.y.z -m "x.y.z"
git push origin vx.y.z
```

> A GitHub Action will **build**, **publish to PyPI** (Trusted Publishing), **create a GitHub Release** with artifacts, and **deploy versioned docs** with `mike`.
