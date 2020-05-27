import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ecuframework",
    version="0.0.3",
    author="Tommaso Viciani",
    author_email="vicianitommaso17@gmail.com",
    description="The ECU framework is a project that wants to simplify writing for Raspberry applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tommasoviciani/ecuframework.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)