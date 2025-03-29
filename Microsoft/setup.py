#!/usr/bin/env python3
"""
Setup script for the Microsoft Advanced Query Processor.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if not line.startswith("#")]

# Get core, azure, and ms365 requirements
core_requirements = [req for req in requirements 
                    if not req.startswith("azure-") 
                    and not req.startswith("msal") 
                    and req != "requests>=2.26.0"
                    and not req.startswith("fastapi")
                    and not req.startswith("uvicorn")
                    and not req.startswith("pydantic")
                    and not req.startswith("python-dotenv")]

azure_requirements = [req for req in requirements if req.startswith("azure-")]
ms365_requirements = ["msal>=1.16.0", "requests>=2.26.0"]
prod_requirements = [req for req in requirements 
                    if req.startswith("fastapi")
                    or req.startswith("uvicorn")
                    or req.startswith("pydantic")
                    or req.startswith("python-dotenv")]

setup(
    name="microsoft-query-processor",
    version="1.0.0",
    author="Microsoft Advanced Query Processor Team",
    author_email="example@microsoft.com",
    description="Production-ready query processor with multi-modal anomaly detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/importstring/microsoft-challenge-demo",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=core_requirements,
    extras_require={
        "azure": azure_requirements,
        "ms365": ms365_requirements,
        "production": prod_requirements,
        "all": azure_requirements + ms365_requirements + prod_requirements
    },
    entry_points={
        "console_scripts": [
            "query-processor=query_processor.main:main",
        ],
    },
) 