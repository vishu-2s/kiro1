# GitHub MCP Server Troubleshooting

## Error: "Connection closed" (MCP error -32000)

This means the MCP server process is starting but immediately crashing.

## Common Causes & Solutions

### 1. Check if `uv` is installed

**Test:**
```powershell
uv --version
```

**If not installed:**
```powershell
# Install uv (Python package manager)
irm https://astral.sh/uv/install.ps1 | iex

# Or using pip
pip install uv
```

### 2. Install the GitHub MCP Server

The server needs to be installed first:

```powershell
# Install mcp-server-github
uvx --from mcp-server-github mcp-server-github --version
```

Or:
```powershell
pip install mcp-server-github
```

### 3. Test the Server Manually

Try running the server directly to see the error:

```powershell
# Set the token
$env:GITHUB_PERSONAL_ACCESS_TOKEN="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"

# Run the server
uvx mcp-server-github
```

This will show you the actual error message.

### 4. Alternative: Use npx instead of uvx

If `uvx` is problematic, try using `npx` (Node.js):

**Install Node.js first** (if not installed):
- Download from: https://nodejs.org/

**Then update mcp.json:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 5. Check Token Validity

Test if your token works:

```powershell
# Test GitHub API with your token
$headers = @{
    "Authorization" = "Bearer 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"
}
Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
```

If this fails, your token is invalid or expired.

### 6. Simplified Configuration (Minimal)

Try this minimal configuration first:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      }
    }
  }
}
```

## Step-by-Step Fix

### Step 1: Install Prerequisites

**Option A: Using Node.js (Recommended for Windows)**
```powershell
# Check if Node.js is installed
node --version

# If not, download from: https://nodejs.org/
```

**Option B: Using Python uv**
```powershell
# Install uv
pip install uv

# Verify
uv --version
```

### Step 2: Choose Configuration

**For Node.js (npx):**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      }
    }
  }
}
```

**For Python (uvx):**
```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      }
    }
  }
}
```

### Step 3: Update mcp.json

1. Open: `C:\Users\VISHAKHA\.kiro\settings\mcp.json`
2. Paste the configuration (choose npx or uvx)
3. Save the file

### Step 4: Restart Kiro

- Close and reopen Kiro IDE
- Or use Command Palette → "MCP: Reconnect Servers"

### Step 5: Check MCP Logs

1. Open Command Palette (Ctrl+Shift+P)
2. Search for "MCP Logs"
3. Look for detailed error messages

## Common Error Messages

### "uvx: command not found"
**Solution:** Install `uv` or use `npx` instead

### "mcp-server-github not found"
**Solution:** 
```powershell
pip install mcp-server-github
```

### "Invalid token"
**Solution:** Generate a new token at https://github.com/settings/tokens

### "Permission denied"
**Solution:** Token needs these scopes:
- `repo` (for private repos)
- `public_repo` (for public repos)

## Recommended Solution for Windows

Use **npx** (Node.js) instead of **uvx**:

1. **Install Node.js:**
   - Download: https://nodejs.org/
   - Install with default options

2. **Update mcp.json:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      }
    }
  }
}
```

3. **Restart Kiro**

This is more reliable on Windows!

## Verification

After fixing, test with:
```
Ask Kiro: "Can you search GitHub for repositories about 'security analysis'?"
```

If it works, you'll see GitHub search results!

## Still Not Working?

1. Check MCP logs for specific error
2. Try disabling and re-enabling the server
3. Verify Node.js or uv is in PATH
4. Try generating a new GitHub token

## Quick Commands

```powershell
# Check installations
node --version
npm --version
uv --version

# Test GitHub token
$headers = @{"Authorization" = "Bearer YOUR_TOKEN"}
Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers

# Install Node.js MCP server manually
npm install -g @modelcontextprotocol/server-github
```

---

**Recommended: Use npx (Node.js) on Windows - it's more reliable than uvx!**
