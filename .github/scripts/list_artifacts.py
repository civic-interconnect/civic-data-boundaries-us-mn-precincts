"""List artifacts in dist/ created by the build process."""
# .github/scripts/list_artifacts.py

from pathlib import Path
import sys

DIST = Path("dist")


def main() -> int:
    """List the distribution artifacts created by the build process."""
    if not DIST.exists():
        print("ERROR: dist/ does not exist")
        return 1

    files = sorted(DIST.glob("*"))
    if not files:
        print("ERROR: dist/ is empty")
        return 1

    print("Dist files:")
    for f in files:
        print(" -", f)

    wheels = sorted(DIST.glob("*.whl"))
    sdists = sorted(DIST.glob("*.tar.gz"))

    if not wheels:
        print("ERROR: No wheel (*.whl) found in dist/")
        return 1
    if not sdists:
        print("ERROR: No sdist (*.tar.gz) found in dist/")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
