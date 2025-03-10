from setuptools import setup, find_packages

setup(
    name="clip_for_humanists",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=1.7.1",
        "transformers>=4.5.0",
        "pillow>=8.0.0",
        "numpy>=1.19.0",
        "pandas>=1.1.0",
        "matplotlib>=3.3.0",
        "folium>=0.12.0",
        "geopy>=2.1.0",
        "tqdm>=4.50.0",
        "ipywidgets>=7.6.0",
    ],
    python_requires=">=3.7",
)
