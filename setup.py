"""Setup script for the grafana-loki-mcp package."""

import os
import re

# mypy: ignore-errors
from setuptools import find_packages, setup

# Read version from __version__.py
with open(os.path.join("grafana_loki_mcp", "__version__.py"), encoding="utf-8") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read long description from README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="grafana-loki-mcp",
    version=version,
    description="A FastMCP server for querying Loki logs from Grafana",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="tumf",
    author_email="tumf@no-reply.github.com",
    url="https://github.com/tumf/grafana-loki-mcp",
    packages=find_packages(),
    py_modules=[],
    install_requires=[
        "fastmcp>=0.1.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.0.270",
            "types-requests>=2.25.0",
            "types-setuptools",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "grafana-loki-mcp=grafana_loki_mcp.__main__:main",
        ],
    },
)
