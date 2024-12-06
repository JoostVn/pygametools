from setuptools import setup, find_packages

setup(
    name="pygametools",
    version="0.1.0",
    packages=[
        "pygametools"
    ],
    package_dir={
        "pygametools":"src/pygametools"
    },
    include_package_data=True,
    package_data={
        "src.pygametools.gui.themes": ["*.json"],
        "src.pygametools.gui.icons": ["*.png"]
    },
)