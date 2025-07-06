"""Setup script for CLIP for Humanists."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = []

setup(
    name="clip-for-humanists",
    version="2.0.0",
    author="CLIP for Humanists Project",
    description="Advanced visual semiotic analysis using CLIP with spatial autocorrelation detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clip-for-humanists/clip-for-humanists",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Sociology :: History",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "full": ["libpysal>=4.7.0", "esda>=2.4.3", "pysal>=2.7.0", "geopandas>=0.13.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0", "black>=23.0.0", "flake8>=6.0.0"],
        "viz": ["plotly>=5.15.0", "bokeh>=3.2.0", "seaborn>=0.12.0"],
    },
    entry_points={
        "console_scripts": [
            "clip-humanists=clip_humanists.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "clip_humanists": ["config/*.yaml"],
    },
)