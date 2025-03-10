from setuptools import setup

setup(
    name="grafana-loki-mcp",
    version="0.1.0",
    description="A FastMCP server for querying Loki logs from Grafana",
    author="OpenHands",
    author_email="openhands@all-hands.dev",
    py_modules=["server"],
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
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
