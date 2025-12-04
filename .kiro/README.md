# Kiro Configuration for Multi-Agent Security Analysis System

This directory contains Kiro IDE configuration files that enhance your development workflow with automated hooks, context-aware steering documents, and MCP integrations.

## 📁 Directory Structure

```
.kiro/
├── hooks/                    # Agent hooks for automation
├── steering/                 # Context documents for AI assistance
├── settings/                 # Kiro settings (MCP, etc.)
├── specs/                    # Feature specifications
└── README.md                 # This file
```

## 🪝 Agent Hooks

Agent hooks automate common tasks and workflows. Located in `.kiro/hooks/`.

### Available Hooks

#### 1. **Run Tests on Save** (`run-tests-on-save.json`)
- **Trigger**: When any Python file is saved
- **Action**: Runs pytest on the saved file
- **Status**: ✅ Enabled
- **Use Case**: Immediate feedback on code changes

#### 2. **Security Scan on Commit** (`security-scan-on-commit.json`)
- **Trigger**: Before committing package files (package.json, requirements.txt, setup.py)
- **Action**: Asks Kiro to scan for malicious packages
- **Status**: ⏸️ Disabled (enable when needed)
- **Use Case**: Catch malicious dependencies before they enter the repo

#### 3. **Update Malicious Package Database** (`update-malicious-db.json`)
- **Trigger**: Manual button click
- **Action**: Runs `python update_constants.py --force`
- **Status**: ✅ Enabled
- **Use Case**: Keep malicious package database up-to-date

#### 4. **Run Property-Based Tests** (`run-property-tests.json`)
- **Trigger**: Manual button click
- **Action**: Runs Hypothesis property tests with statistics
- **Status**: ✅ Enabled
- **Use Case**: Validate correctness properties across random inputs

### Managing Hooks

**View Hooks**: Open the "Agent Hooks" section in Kiro's explorer view

**Enable/Disable**: Edit the `"enabled"` field in the hook JSON file

**Create New Hook**: Use Command Palette → "Open Kiro Hook UI"

## 🧭 Steering Documents

Steering documents provide context-aware guidance to Kiro. Located in `.kiro/steering/`.

### Available Steering Docs

#### 1. **Project Overview** (`project-overview.md`)
- **Inclusion**: Always included in context
- **Content**: Architecture, principles, development focus, security guidelines
- **Use Case**: Helps Kiro understand the project structure and conventions

#### 2. **Testing Guidelines** (`testing-guidelines.md`)
- **Inclusion**: Automatically included when working with test files
- **Pattern**: `test_*.py` or `*_test.py`
- **Content**: Test organization, property-based testing, fixtures, mocking
- **Use Case**: Ensures consistent test writing practices

#### 3. **Analyzer Development Guide** (`analyzer-development.md`)
- **Inclusion**: Automatically included when working with analyzer files
- **Pattern**: `*_analyzer.py` or `ecosystem_analyzer.py`
- **Content**: Step-by-step guide for adding new ecosystem analyzers
- **Use Case**: Streamlines adding support for new languages (Java, Go, Rust, etc.)

### Creating Custom Steering Docs

```markdown
---
inclusion: fileMatch
fileMatchPattern: "pattern*.py"
---

# Your Steering Document Title

Content here will be included when files matching the pattern are in context.
```

**Inclusion Types**:
- `always`: Always included
- `fileMatch`: Included when matching files are open
- `manual`: Included only when explicitly referenced with `#`

## 🔌 MCP Integration

Model Context Protocol (MCP) servers extend Kiro's capabilities. Configured in `.kiro/settings/mcp.json`.

### Configured MCP Servers

#### 1. **Filesystem Server**
- **Purpose**: Read project files and directories
- **Scope**: `tools/` and `tests/` directories
- **Auto-approved**: `read_file`, `list_directory`
- **Use Case**: Kiro can analyze your codebase structure

#### 2. **GitHub Server**
- **Purpose**: Search repositories and read files from GitHub
- **Auth**: Uses `GITHUB_TOKEN` from environment
- **Auto-approved**: `search_repositories`, `get_file_contents`
- **Use Case**: Research similar projects, check for known vulnerabilities

#### 3. **Fetch Server**
- **Purpose**: Fetch content from URLs
- **Auto-approved**: `fetch`
- **Use Case**: Check package registries, fetch security advisories

### Installing MCP Servers

MCP servers use `uvx` (part of the `uv` Python package manager):

```bash
# Install uv (if not already installed)
# On macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Servers are automatically downloaded when first used
```

### Managing MCP Servers

**View Servers**: Check the "MCP Server" view in Kiro's feature panel

**Reconnect**: Servers auto-reconnect on config changes

**Disable**: Set `"disabled": true` in the server config

**Add Auto-approve**: Add tool names to the `"autoApprove"` array

## 📋 Specs

Feature specifications follow the spec-driven development workflow. Located in `.kiro/specs/`.

### Current Specs

1. **npm-script-analysis**: Original npm security analysis feature
2. **production-ready-enhancements**: Current focus - caching, Python support, reputation scoring, tests, CI/CD

### Working with Specs

**Start Task**: Open `tasks.md` → Click "Start task" next to any task

**Update Spec**: Ask Kiro to update requirements, design, or tasks

**Create New Spec**: Ask Kiro to create a new spec for a feature

## 🧪 Quick Test

**Run the diagnostic script to verify everything is set up:**

```bash
python .kiro/diagnose.py
```

This will check:
- ✅ Directory structure
- ✅ Agent Hooks configuration
- ✅ Steering Documents setup
- ✅ MCP configuration
- ✅ Dependencies (uv installation)
- ✅ Environment variables

**For detailed testing instructions, see:** `.kiro/TESTING_GUIDE.md`

## 🚀 Quick Start

### 1. Enable Useful Hooks
```bash
# Edit hook files to enable/disable
code .kiro/hooks/security-scan-on-commit.json
# Change "enabled": false to "enabled": true
```

### 2. Install MCP Dependencies
```bash
# Install uv for MCP servers
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Set Environment Variables
```bash
# Add to your .env file
GITHUB_TOKEN=your_github_token_here
```

### 4. Start Using Kiro
- Open any test file → Testing guidelines auto-load
- Open any analyzer file → Analyzer guide auto-load
- Click "🔄 Update Malicious DB" button → Database updates
- Save a Python file → Tests run automatically (if enabled)

## 💡 Tips

### For Development
- Keep steering docs updated as architecture evolves
- Add new hooks for repetitive tasks
- Use manual hooks for one-off operations

### For Testing
- Use the "Run Property Tests" hook to validate correctness
- Enable "Run Tests on Save" for TDD workflow
- Create fixtures in `tests/fixtures/` for consistent testing

### For Security
- Enable "Security Scan on Commit" before releases
- Regularly update malicious package database
- Review MCP auto-approvals periodically

## 🔧 Troubleshooting

### Hooks Not Running
- Check `"enabled": true` in hook JSON
- Verify file patterns match your files
- Check Kiro output panel for errors

### MCP Servers Not Working
- Ensure `uv` is installed: `uv --version`
- Check environment variables are set
- View MCP logs in Kiro's MCP Server panel

### Steering Docs Not Loading
- Verify file pattern in frontmatter
- Check `inclusion` type is correct
- Ensure file is in `.kiro/steering/` directory

## 📚 Resources

- [Kiro Hooks Documentation](https://docs.kiro.ai/hooks)
- [Kiro Steering Documentation](https://docs.kiro.ai/steering)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Hypothesis Testing](https://hypothesis.readthedocs.io)

## 🤝 Contributing

When adding new features:
1. Update relevant steering documents
2. Create hooks for common workflows
3. Add MCP servers if external data is needed
4. Document in this README
