# GitHub MCP Server Setup Guide

## Your GitHub Token
From your `.env` file:
```
GITHUB_PAT_TOKEN=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
```

## MCP Configuration Location
```
C:\Users\VISHAKHA\.kiro\settings\mcp.json
```

## How to Update MCP Configuration

### Option 1: Manual Edit (Recommended)
1. Open the file in a text editor:
   ```
   C:\Users\VISHAKHA\.kiro\settings\mcp.json
   ```

2. Add or update the GitHub MCP server configuration:
   ```json
   {
     "mcpServers": {
       "github": {
         "command": "uvx",
         "args": ["mcp-server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
         },
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

### Option 2: Complete MCP Configuration Example
If you want a full configuration with multiple MCP servers:

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      },
      "disabled": false,
      "autoApprove": []
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## What This Enables

With the GitHub MCP server configured, you'll be able to:
- 🔍 Search GitHub repositories
- 📂 Browse repository contents
- 📄 Read file contents from GitHub
- 🔀 List branches and commits
- 📊 Get repository information
- 🐛 Search issues and pull requests

## Verification Steps

### 1. Save the Configuration
After editing `mcp.json`, save the file.

### 2. Restart Kiro
The MCP servers will reconnect automatically, or you can:
- Use Command Palette → "MCP: Reconnect Servers"
- Or restart Kiro IDE

### 3. Test the Connection
Try using GitHub MCP tools in Kiro:
```
Ask Kiro: "Can you search for repositories about security analysis on GitHub?"
```

## Troubleshooting

### Issue: "uvx not found"
**Solution:** Install `uv` (Python package manager):
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Or using pip
pip install uv
```

### Issue: "Invalid token"
**Check:**
1. Token is correct (no extra spaces)
2. Token has required permissions:
   - `repo` (for private repos)
   - `public_repo` (for public repos)
   - `read:org` (optional, for organization access)

**Generate new token:**
https://github.com/settings/tokens

### Issue: MCP server not starting
**Check MCP logs:**
- Open Command Palette
- Search for "MCP Logs"
- Look for error messages

## Security Notes

⚠️ **Important:**
- Never commit `mcp.json` with tokens to version control
- The file at `C:\Users\VISHAKHA\.kiro\settings\mcp.json` is user-level (not in workspace)
- This is the correct location for sensitive credentials

## Alternative: Environment Variable

Instead of hardcoding the token, you can use an environment variable:

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT_TOKEN}"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Then set the environment variable in your system.

## Quick Copy-Paste

**Your specific configuration (ready to paste):**
```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "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"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Steps Summary

1. ✅ Open `C:\Users\VISHAKHA\.kiro\settings\mcp.json`
2. ✅ Paste the configuration above
3. ✅ Save the file
4. ✅ Restart Kiro or reconnect MCP servers
5. ✅ Test by asking Kiro to search GitHub

**Status: Ready to configure! 🚀**
