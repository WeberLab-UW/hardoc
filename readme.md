# Hardoc

An analyzer for Open Source Hardware documentation quality.

## Features

- Documentation quality analysis
- BOM (Bill of Materials) validation
- Multi-repository support
- Quality metrics and scoring
- Structured output formats (JSON, CSV)

## Installation

```bash
pip install hardoc
```

## Quick Start

```python
from hardoc import analyze_repo

# Analyze a single repository
results = analyze_repo("https://github.com/username/repo")
print(results.summary())

# Analyze multiple repositories
repos = ["repo1", "repo2", "repo3"]
batch_results = analyze_repos(repos)
batch_results.export_csv("analysis_results.csv")
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hardoc
cd hardoc
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
