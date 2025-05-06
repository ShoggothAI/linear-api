import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="linear-api",
    version="0.1.0",
    author="Motley Stories AG",
    author_email="egor@motley.ai",
    description="A set of Python utilities for calling the Linear API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ShoggothAI/linear-api",
    project_urls={
        "Bug Tracker": "https://github.com/ShoggothAI/linear-api/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(exclude=["tests", "playground"]),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.25.0",
    ],
)
