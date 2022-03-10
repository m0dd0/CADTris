import setuptools
from pathlib import Path

README = (Path(__file__).parent / "README.md").read_text()


setuptools.setup(
    name="CADTris",
    description="Utilizing Fusion360 to play Tetris.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Moritz Hesche",
    author_email="mo.hesche@gmail.com",
    url="https://github.com/m0dd0/CADTris",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    project_urls={},
    python_requires=">=3.7",  # current (01.2021) python version used by Fusion360
    install_requires=[],
    include_package_data=True,  # needs to be kept even setuptools_scm is used !!!
    # including pacakge_data is managed automatically by setuptools_scm which is
    # also defined as buid_dependency in pyproject.toml
    use_scm_version=True,
    extras_require={"dev": ["build", "black", "pylint", "pytest"]},
)
