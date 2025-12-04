# Testing & Debugging Kiro Features

This guide shows you how to verify that Agent Hooks, Steering Documents, and MCP Servers are working correctly.

## 🪝 Testing Agent Hooks

### Method 1: Check the Agent Hooks Panel

1. **Open the Agent Hooks View**
   - Look for "Agent Hooks" section in Kiro's Explorer sidebar
   - Or use Command Palette: `Ctrl+Shift+P` → "Kiro: Show Agent Hooks"

2. **What to Look For**
   - ✅ Green checkmark = Hook is enabled and loaded
   - ⏸️ Gray icon = Hook is disabled
   - ❌ Red X = Hook has errors

3. **View Hook Details**
   - Click on any hook to see its configuration
   - Check the trigger conditions
   - Verify the action commands

### Method 2: Test Manual Hooks (Buttons)

**Test "Update Malicious DB" Hook:**
```bash
# 1. Look for the button in Agent Hooks panel
# 2. Click "🔄 Update Malicious DB"
# 3. Check Kiro's Output panel for execution logs
```

**Expected Output:**
```
[Agent Hook] Executing: python update_constants.py --force
[Output] Updating malicious package database...
[Output] Database updated successfully
```

**Test "Run Property Tests" Hook:**
```bash
# 1. Click "🧪 Run Property Tests" button
# 2. Watch the terminal/output panel
```

**Expected Output:**
```
[Agent Hook] Executing: pytest -k property -v --hypothesis-show-statistics
======================== test session starts ========================
collected X items
...
```

### Method 3: Test File-Based Hooks

**Test "Run Tests on Save" Hook:**

1. Open any Python file (e.g., `tools/cache_manager.py`)
2. Make a small change (add a comment)
3. Save the file (`Ctrl+S`)
4. **Watch for:**
   - Kiro's Output panel shows: `[Agent Hook] File saved: tools/cache_manager.py`
   - Terminal shows pytest running
   - Test results appear

**If nothing happens:**
- Check if hook is enabled: Open `.kiro/hooks/run-tests-on-save.json`
- Verify `"enabled": true`
- Check file pattern matches: `"filePattern": "**/*.py"`

### Method 4: Check Kiro Output Panel

1. **Open Output Panel**
   - View → Output (or `Ctrl+Shift+U`)
   - Select "Kiro" from the dropdown

2. **Look for Hook Execution Logs**
   ```
   [Agent Hooks] Loaded 4 hooks
   [Agent Hooks] Registered hook: Run Tests on Save
   [Agent Hooks] Registered hook: Security Scan on Commit
   [Agent Hooks] Registered hook: Update Malicious DB
   [Agent Hooks] Registered hook: Run Property Tests
   
   [Agent Hook] Triggered: Run Tests on Save
   [Agent Hook] Executing command: pytest tools/cache_manager.py -v --tb=short
   [Agent Hook] Exit code: 0
   ```

### Method 5: Manual Testing

**Test hooks manually to verify commands work:**

```bash
# Test the "Run Tests on Save" command
pytest tools/cache_manager.py -v --tb=short

# Test the "Update Malicious DB" command
python update_constants.py --force

# Test the "Run Property Tests" command
pytest -k property -v --hypothesis-show-statistics
```

If these commands work manually but hooks don't trigger, there's a hook configuration issue.

## 🧭 Testing Steering Documents

### Method 1: Check Context Inclusion

1. **Open a Test File**
   - Open `tests/test_cache_manager.py`
   - Ask Kiro: "What testing guidelines should I follow?"
   - **Expected:** Kiro references testing-guidelines.md

2. **Open an Analyzer File**
   - Open `tools/npm_analyzer.py`
   - Ask Kiro: "How do I add a new ecosystem analyzer?"
   - **Expected:** Kiro references analyzer-development.md

3. **Ask About Security**
   - Ask Kiro: "What are critical security patterns in Python?"
   - **Expected:** Kiro references security-patterns.md

### Method 2: Verify File Pattern Matching

**Check which steering docs are active:**

1. Open different file types and note which docs load:
   - `test_*.py` → Should load `testing-guidelines.md`
   - `*_analyzer.py` → Should load `analyzer-development.md`
   - Any file → Should always load `project-overview.md` and `security-patterns.md`

2. **Ask Kiro to confirm:**
   ```
   "What steering documents are currently loaded?"
   ```

### Method 3: Check Steering Directory

```bash
# List all steering documents
ls -la .kiro/steering/

# Expected output:
# analyzer-development.md
# project-overview.md
# security-patterns.md
# testing-guidelines.md
```

**Verify frontmatter:**
```bash
# Check if frontmatter is correct
head -n 5 .kiro/steering/testing-guidelines.md
```

**Expected:**
```markdown
---
inclusion: fileMatch
fileMatchPattern: "test_*.py|*_test.py"
---
```

### Method 4: Test Context Awareness

**Test 1: Project Overview (Always Loaded)**
```
Ask Kiro: "What is the plugin-based architecture in this project?"
Expected: Detailed answer about EcosystemAnalyzer base class
```

**Test 2: Testing Guidelines (Conditional)**
```
1. Open: tests/test_cache_manager.py
2. Ask Kiro: "How should I structure property-based tests?"
Expected: Answer with Hypothesis examples and feature tagging
```

**Test 3: Analyzer Development (Conditional)**
```
1. Open: tools/npm_analyzer.py
2. Ask Kiro: "What methods must I implement for a new analyzer?"
Expected: List of abstract methods from EcosystemAnalyzer
```

**Test 4: Security Patterns (Always Loaded)**
```
Ask Kiro: "What severity is os.system() in Python?"
Expected: "Critical - Remote code execution"
```

## 🔌 Testing MCP Servers

### Method 1: Check MCP Server Status

1. **Open MCP Server View**
   - Look for "MCP Servers" in Kiro's sidebar
   - Or Command Palette: `Ctrl+Shift+P` → "Kiro: Show MCP Servers"

2. **Check Server Status**
   - 🟢 Green = Connected and running
   - 🟡 Yellow = Starting/reconnecting
   - 🔴 Red = Error or disconnected
   - ⚪ Gray = Disabled

3. **View Server Details**
   - Click on each server to see:
     - Connection status
     - Available tools
     - Recent activity
     - Error logs (if any)

### Method 2: Test MCP Tools

**Test Filesystem Server:**
```
Ask Kiro: "List all files in the tools/ directory"
Expected: Kiro uses mcp-server-filesystem to list files
```

**Test GitHub Server:**
```
Ask Kiro: "Search GitHub for Python security analysis projects"
Expected: Kiro uses mcp-server-github to search
```

**Test Fetch Server:**
```
Ask Kiro: "Fetch the latest npm registry data for 'express'"
Expected: Kiro uses mcp-server-fetch to get data
```

### Method 3: Check MCP Logs

1. **Open Kiro Output Panel**
   - View → Output
   - Select "MCP Servers" from dropdown

2. **Look for Connection Logs**
   ```
   [MCP] Starting server: filesystem
   [MCP] Server filesystem connected
   [MCP] Available tools: read_file, list_directory, search_files
   
   [MCP] Starting server: github
   [MCP] Server github connected
   [MCP] Available tools: search_repositories, get_file_contents
   
   [MCP] Starting server: fetch
   [MCP] Server fetch connected
   [MCP] Available tools: fetch
   ```

3. **Look for Tool Usage**
   ```
   [MCP] Tool called: read_file
   [MCP] Arguments: {"path": "tools/cache_manager.py"}
   [MCP] Result: Success (1234 bytes)
   ```

### Method 4: Verify MCP Installation

**Check if `uv` is installed:**
```bash
uv --version
# Expected: uv 0.x.x
```

**If not installed:**
```bash
# On macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Test uvx command:**
```bash
uvx --help
# Should show uvx help text
```

### Method 5: Manual MCP Server Test

**Test filesystem server manually:**
```bash
# This won't work directly, but verifies uvx can find the package
uvx mcp-server-filesystem --help
```

**Check MCP configuration:**
```bash
# View your MCP config
cat .kiro/settings/mcp.json

# Verify JSON is valid
python -m json.tool .kiro/settings/mcp.json
```

### Method 6: Test with Auto-Approved Tools

**Filesystem server (auto-approved):**
```
Ask Kiro: "Read the file tools/cache_manager.py"
Expected: Kiro reads it without asking permission
```

**GitHub server (auto-approved):**
```
Ask Kiro: "Search for repositories about supply chain security"
Expected: Kiro searches without asking permission
```

**Fetch server (auto-approved):**
```
Ask Kiro: "Fetch https://registry.npmjs.org/express"
Expected: Kiro fetches without asking permission
```

## 🐛 Troubleshooting

### Hooks Not Working

**Problem:** Hook doesn't trigger when expected

**Solutions:**
1. Check if enabled: `"enabled": true` in hook JSON
2. Verify file pattern matches your files
3. Check Kiro Output panel for errors
4. Test command manually in terminal
5. Restart Kiro IDE

**Problem:** Manual hook button doesn't appear

**Solutions:**
1. Check hook has `"trigger": {"type": "manual"}`
2. Verify hook JSON is valid (use JSON validator)
3. Reload Agent Hooks view
4. Check Kiro Output for parsing errors

### Steering Docs Not Loading

**Problem:** Kiro doesn't reference steering docs

**Solutions:**
1. Verify frontmatter syntax (YAML between `---`)
2. Check file pattern matches: `fileMatchPattern: "test_*.py"`
3. Ensure file is in `.kiro/steering/` directory
4. Test with `inclusion: always` temporarily
5. Ask Kiro explicitly: "What steering docs are loaded?"

**Problem:** Steering doc has wrong content

**Solutions:**
1. Edit the file in `.kiro/steering/`
2. Save changes
3. Reload window or restart Kiro
4. Steering docs update automatically

### MCP Servers Not Connecting

**Problem:** MCP server shows as disconnected

**Solutions:**
1. Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Check environment variables (e.g., `GITHUB_TOKEN`)
3. Verify JSON syntax in `.kiro/settings/mcp.json`
4. Check MCP logs in Output panel
5. Try reconnecting: Right-click server → "Reconnect"

**Problem:** MCP tools require approval every time

**Solutions:**
1. Add tool names to `"autoApprove"` array in MCP config
2. Example: `"autoApprove": ["read_file", "list_directory"]`
3. Save config (servers auto-reconnect)

**Problem:** `uv` command not found

**Solutions:**
1. Install uv (see commands above)
2. Restart terminal/IDE after installation
3. Check PATH includes uv: `echo $PATH` (Linux/Mac) or `echo %PATH%` (Windows)
4. Try full path: `/home/user/.cargo/bin/uvx` (adjust for your system)

## ✅ Quick Verification Checklist

### Agent Hooks
- [ ] Hooks appear in Agent Hooks panel
- [ ] Manual hooks show buttons
- [ ] File-based hooks trigger on save
- [ ] Commands execute successfully
- [ ] Output appears in Kiro Output panel

### Steering Documents
- [ ] Files exist in `.kiro/steering/`
- [ ] Frontmatter is valid YAML
- [ ] File patterns match your files
- [ ] Kiro references docs in responses
- [ ] Context changes based on open files

### MCP Servers
- [ ] `uv` is installed (`uv --version`)
- [ ] Servers show as connected (green)
- [ ] Tools are listed for each server
- [ ] Kiro can use MCP tools
- [ ] Auto-approved tools work without prompts

## 📊 Success Indicators

**You'll know everything is working when:**

1. **Hooks:** Save a Python file → Tests run automatically
2. **Steering:** Open a test file → Ask about testing → Kiro references guidelines
3. **MCP:** Ask Kiro to list files → It uses filesystem server

**Example successful interaction:**
```
You: "List files in tools/ directory"
Kiro: [Uses mcp-server-filesystem]
      "Here are the files in tools/:
      - cache_manager.py
      - npm_analyzer.py
      - python_analyzer.py
      ..."

You: "What testing guidelines should I follow?"
Kiro: [References testing-guidelines.md]
      "Based on the project's testing guidelines:
      1. Use pytest for unit tests
      2. Use Hypothesis for property-based tests
      ..."
```

## 🎯 Next Steps

Once verified:
1. Enable hooks you want to use regularly
2. Customize steering docs for your workflow
3. Add more MCP servers as needed
4. Create custom hooks for your tasks

Need help? Check `.kiro/README.md` for detailed documentation!
