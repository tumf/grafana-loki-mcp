.PHONY: lint format test clean install update fix-lint build publish test-publish coverage bump-patch bump-minor bump-major release

# Python version
PYTHON := python3

# Virtual environment
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python

# Source directories
SRC_DIRS := .

# Default target
all: lint format test

# Linting
lint:
	@echo "Running ruff..."
	uv run ruff check $(SRC_DIRS)
	@echo "Running mypy..."
	uv run mypy $(SRC_DIRS)

# Fix linting errors
fix-lint:
	@echo "Fixing ruff errors..."
	uv run ruff check --fix $(SRC_DIRS)
	@echo "Running black..."
	uv run black $(SRC_DIRS)
	@echo "Running isort..."
	uv run isort $(SRC_DIRS)

# Formatting
format:
	@echo "Running black..."
	uv run black $(SRC_DIRS)
	@echo "Running isort..."
	uv run isort $(SRC_DIRS)

# Testing
test:
	@echo "Running tests..."
	uv run pytest

# Coverage
coverage:
	@echo "Running tests with coverage..."
	uv run pytest --cov=grafana_loki_mcp --cov-report=term --cov-report=xml --cov-report=html

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage coverage.xml

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv pip install -e ".[dev]"

# Update dependencies
update:
	@echo "Updating dependencies..."
	uv pip install --upgrade -e ".[dev]"

# Build package
build: clean
	@echo "Building package..."
	uv run python -m build

# Test publish to TestPyPI
test-publish: build
	@echo "Publishing to TestPyPI..."
	uv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Publish to PyPI
publish: build
	@echo "Publishing to PyPI..."
	uv run twine upload dist/*

# Version bumping
VERSION_FILE := grafana_loki_mcp/__version__.py

# Helper function to update version
define update_version
	@echo "Updating version to $(1)"
	@sed -i.bak 's/__version__ = "[^"]*"/__version__ = "$(1)"/' $(VERSION_FILE)
	@rm -f $(VERSION_FILE).bak
	@git add $(VERSION_FILE)
	@git commit -m "Bump version to $(1)"
	@git tag -a v$(1) -m "Version $(1)"
	@echo "Version updated to $(1). Don't forget to push with: git push && git push --tags"
endef

# Get current version (macOS compatible)
CURRENT_VERSION := $(shell grep -o '"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*[^"]*"' $(VERSION_FILE) | tr -d '"')
VERSION_BASE := $(shell echo $(CURRENT_VERSION) | sed -E 's/([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
VERSION_SUFFIX := $(shell echo $(CURRENT_VERSION) | grep -o -- "-[a-zA-Z0-9]\+" || echo "")
MAJOR := $(shell echo $(VERSION_BASE) | cut -d. -f1)
MINOR := $(shell echo $(VERSION_BASE) | cut -d. -f2)
PATCH := $(shell echo $(VERSION_BASE) | cut -d. -f3)
BETA_NUM := $(shell echo $(CURRENT_VERSION) | grep -o "beta[0-9]\+" | grep -o "[0-9]\+" || echo "0")

# Bump patch version (0.0.x)
bump-patch:
	$(eval NEW_PATCH := $(shell echo $$(($(PATCH) + 1))))
	$(eval NEW_VERSION := $(MAJOR).$(MINOR).$(NEW_PATCH))
	$(call update_version,$(NEW_VERSION))

# Bump minor version (0.x.0)
bump-minor:
	$(eval NEW_MINOR := $(shell echo $$(($(MINOR) + 1))))
	$(eval NEW_VERSION := $(MAJOR).$(NEW_MINOR).0)
	$(call update_version,$(NEW_VERSION))

# Bump major version (x.0.0)
bump-major:
	$(eval NEW_MAJOR := $(shell echo $$(($(MAJOR) + 1))))
	$(eval NEW_VERSION := $(NEW_MAJOR).0.0)
	$(call update_version,$(NEW_VERSION))

# Bump beta version (x.x.x-beta)
bump-beta:
	$(eval NEW_BETA_NUM := $(shell echo $$(($(BETA_NUM) + 1))))
	$(eval NEW_VERSION := $(VERSION_BASE)-beta$(NEW_BETA_NUM))
	$(call update_version,$(NEW_VERSION))

# Remove beta suffix for release (x.x.x-betaX -> x.x.x)
release:
	$(eval NEW_VERSION := $(VERSION_BASE))
	$(call update_version,$(NEW_VERSION))
