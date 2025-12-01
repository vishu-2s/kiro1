# Multi-Agent Security Analysis System

An AI-powered security analysis platform that uses multiple specialized agents to detect malicious packages, vulnerabilities, and supply chain attacks in software projects.

## Features

- **Multi-Agent Architecture**: Specialized AI agents for different security analysis tasks
- **Supply Chain Security**: Comprehensive SBOM analysis and vulnerability detection
- **Visual Security Analysis**: GPT-4 Vision integration for screenshot analysis
- **Automated Threat Intelligence**: Real-time updates from OSV database
- **Comprehensive Reporting**: Detailed incident reports with remediation guidance

## Project Structure

```
multi-agent-security/
├── agents/                 # AI agent implementations
├── tools/                  # Analysis tools and utilities
├── artifacts/              # Sample artifacts and test data
├── screenshots/            # Screenshots for visual analysis
├── outputs/                # Analysis results and reports
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── setup_venv.py         # Virtual environment setup
```

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository and navigate to the project directory
cd multi-agent-security

# Run the setup script to create virtual environment and install dependencies
python setup_venv.py

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Configuration

1. Copy the `.env` file and update with your API keys:
   ```bash
   cp .env .env.local
   ```

2. Edit `.env.local` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here  # Optional
   ```

### 3. Usage

```bash
# Analyze a GitHub repository
python main_github.py --repo https://github.com/owner/repo

# Analyze a local directory
python main_github.py --local /path/to/project

# Get help
python main_github.py --help
```

## Dependencies

The system requires the following main dependencies:

- **pyautogen**: Multi-agent framework
- **openai**: OpenAI API integration
- **requests**: HTTP client for API calls
- **pydantic**: Data validation
- **python-dotenv**: Environment configuration
- **hypothesis**: Property-based testing

See `requirements.txt` for the complete list.

## Configuration Options

The system can be configured through environment variables in the `.env` file:

### Core Configuration
- `OPENAI_API_KEY`: OpenAI API key (required)
- `GITHUB_TOKEN`: GitHub API token (optional)
- `OUTPUT_DIRECTORY`: Directory for analysis results

### Agent Configuration
- `AGENT_TEMPERATURE`: AI model temperature (default: 0.1)
- `AGENT_MAX_TOKENS`: Maximum tokens per response (default: 4096)
- `AGENT_TIMEOUT_SECONDS`: Agent timeout (default: 120)

### Analysis Configuration
- `CACHE_ENABLED`: Enable threat intelligence caching (default: true)
- `CACHE_DURATION_HOURS`: Cache duration (default: 24)
- `ENABLE_OSV_QUERIES`: Enable OSV API queries (default: true)

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest hypothesis

# Run all tests
pytest

# Run property-based tests
pytest -k "property"
```

### Project Status

This project is currently under development. The following components are planned:

- [ ] Core project structure ✓
- [ ] Security signature database
- [ ] SBOM processing tools
- [ ] GitHub integration
- [ ] Local directory analysis
- [ ] AI agent implementations
- [ ] Multi-agent coordination
- [ ] Visual security analysis
- [ ] Comprehensive reporting

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## Support

For questions and support, please open an issue on the project repository.