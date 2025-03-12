# Publishing to PyPI

This document describes how to publish the `grafana-loki-mcp` package to PyPI.

## Prerequisites

Make sure you have the following tools installed:

- Python 3.10 or higher
- `build` and `twine` packages
- `make` command

```bash
pip install build twine
```

## Updating the Version

There are two ways to update the version:

### 1. Using Make commands (recommended)

The project provides convenient make commands to bump the version:

```bash
# Bump patch version (0.1.0 -> 0.1.1)
make bump-patch

# Bump minor version (0.1.0 -> 0.2.0)
make bump-minor

# Bump major version (0.1.0 -> 1.0.0)
make bump-major
```

These commands will:
1. Update the version in `grafana_loki_mcp/__version__.py`
2. Commit the change
3. Create a git tag
4. Remind you to push the changes and tags

After running one of these commands, push the changes:

```bash
git push && git push --tags
```

This will trigger the GitHub Actions workflow to automatically build and publish the package to PyPI.

### 2. Manual update

If you prefer to update the version manually:

1. Update the version in `grafana_loki_mcp/__version__.py`
2. Commit the changes:

```bash
git add grafana_loki_mcp/__version__.py
git commit -m "Bump version to x.y.z"
git tag vx.y.z
git push origin main --tags
```

## Building the Package Locally

Build the package using make:

```bash
make build
```

This will create both source distribution ( `.tar.gz` ) and wheel ( `.whl` ) files in the `dist/` directory.

## Testing the Package Locally

It's recommended to test the package on TestPyPI before publishing to the main PyPI repository:

```bash
make test-publish
```

Then install and test the package from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ grafana-loki-mcp
```

## Publishing to PyPI Manually

Once you've verified that the package works correctly, you can manually upload it to PyPI:

```bash
make publish
```

You'll need to enter your PyPI username and password.

## Automated Publishing with GitHub Actions

The project is configured to automatically publish to PyPI when a new tag is pushed:

1. Update the version using one of the methods above
2. Push the tag to GitHub
3. The GitHub Actions workflow will build and publish the package to PyPI

For this to work, you need to set up a PyPI API token as a GitHub secret named `PYPI_API_TOKEN` .

## Verifying the Publication

After publishing, verify that the package can be installed from PyPI:

```bash
pip install grafana-loki-mcp
```

## Cleaning Up

After publishing, you can clean up the build artifacts:

```bash
make clean
```
