# DocuPR

DocuPR is a Python application that analyzes pull requests (PRs) in a GitHub repository since the previous release, identifies which ones involve user-facing changes, and generates a summary of the documentation updates needed.

> [!IMPORTANT]
> This is a sample app I generated entirely using Cline + Claude 3.7 Sonnet. My goal was to get more familiar with AI coding tools and see if I could create a working app without touching a single line of code by hand. There may be dragons here, so YMMV.

## Features

- **GitHub Integration**: Fetches pull requests made since the last release using the GitHub API.
- **Change Identification**: Analyzes PRs to determine which ones have user-facing changes.
- **OpenAI Integration**: Uses OpenAI's API to analyze changes and summarize documentation updates needed.
- **Security**: Securely stores API keys using environment variables.
- **Performance**: Optimizes API calls and uses asynchronous programming for better performance.
- **Output**: Generates a comprehensive markdown report of documentation updates needed.

## Installation

### Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token
- OpenAI API key

### Setup

1. Clone the repository:

```bash
git clone https://github.com/danbarr/docupr.git
cd docupr
```

2. Set up a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install the package:

```bash
pip install -e .
```

4. Create a `.env` file in the project root with your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file and add your GitHub Personal Access Token and OpenAI API key:

```
# GitHub Personal Access Token
# Create one at: https://github.com/settings/tokens
# Required scopes: repo (to access repository data)
GITHUB_TOKEN=your_github_personal_access_token

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Basic Usage

```bash
# Make sure your virtual environment is activated
python -m docupr analyze https://github.com/username/repo
```

This will:
1. Authenticate with GitHub using your Personal Access Token
2. Fetch PRs since the last release (or last 30 days if no release found)
3. Analyze each PR to determine if it contains user-facing changes
4. Generate a markdown report of documentation updates needed

### Command-line Options

```
Usage: docupr analyze [OPTIONS] REPO_URL

  Analyze a GitHub repository and generate a documentation update report.

  REPO_URL is the URL of the GitHub repository to analyze.

Options:
  --since TEXT       Date to filter PRs by (YYYY-MM-DD). Defaults to latest
                     release date or 30 days ago.
  --release-tag TEXT Release tag to start from. Defaults to latest release.
  --token TEXT       GitHub Personal Access Token. If not provided, will use the token
                     from the .env file.
  --output-dir TEXT  Directory to save reports to. Defaults to current
                     directory.
  --json             Generate a JSON report instead of markdown.
  --help             Show this message and exit.
```

### Examples

Analyze PRs since a specific date:

```bash
python -m docupr analyze https://github.com/username/repo --since 2023-01-01
```

Analyze PRs since a specific release tag:

```bash
python -m docupr analyze https://github.com/username/repo --release-tag v1.0.0
```

Use a different GitHub token than the one in your .env file:

```bash
python -m docupr analyze https://github.com/username/repo --token your_github_token
```

Generate a JSON report:

```bash
python -m docupr analyze https://github.com/username/repo --json
```

## Report Format

The generated markdown report includes:

- Summary of PRs analyzed and user-facing changes found
- List of documentation updates needed
- Detailed analysis of each PR with user-facing changes

Example:

```markdown
# Documentation Update Report for https://github.com/username/repo

Generated on: 2023-03-04 13:45:30

Analyzing PRs since: 2023-01-01

## Summary

Total PRs analyzed: 25
PRs with user-facing changes: 5

## Documentation Updates Needed

### Existing Documentation to Update

- docs/api-reference.md
- docs/user-guide.md

### New Documentation to Create

- docs/new-feature.md

### Suggested Content Updates

- PR #123: Add section on new authentication flow
- PR #456: Update API examples with new parameters

## Detailed PR Analysis

### PR #123: Add new authentication flow

- URL: https://github.com/username/repo/pull/123
- User-facing: Yes
- Reasoning: This PR adds a new OAuth-based authentication flow that users will need to understand.

#### Existing Documentation to Update

- docs/api-reference.md
- docs/user-guide.md

#### Suggested Content

- Add section on OAuth authentication flow
- Include examples of token usage
```

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
docupr/
├── src/
│   ├── __init__.py
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration handling
│   ├── github_client.py   # GitHub API client
│   ├── openai_analyzer.py # OpenAI integration
│   └── report_generator.py # Report generation
├── tests/
├── .env.example
├── docupr.py              # Main entry point
├── README.md
├── requirements.txt
└── setup.py
```

## Security Considerations

- API keys are stored in environment variables, not hardcoded.
- HTTPS is used for all API requests.
- Input validation is performed to prevent injection attacks.
- Error handling is implemented for failed API calls.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
