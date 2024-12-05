from setuptools import setup, find_packages

setup(
    name="hardoc",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.19.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "markdown>=3.3.0",
        "pyyaml>=5.4.0",
        "tabulate>=0.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "mypy>=0.900",
            "flake8>=3.9.0",
        ],
    },
    author="Your Name",
    description="An analyzer for Open Source Hardware documentation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hardoc",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
)
