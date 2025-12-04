#!/usr/bin/env python3
"""
Diagnostic script to verify Kiro features are set up correctly.
Run this to check Agent Hooks, Steering Documents, and MCP configuration.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print a section header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def print_success(text: str):
    """Print a success message."""
    print(f"{GREEN}✓{RESET} {text}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")

def print_error(text: str):
    """Print an error message."""
    print(f"{RED}✗{RESET} {text}")

def print_info(text: str):
    """Print an info message."""
    print(f"{BLUE}ℹ{RESET} {text}")

def check_directory_structure() -> bool:
    """Check if .kiro directory structure exists."""
    print_header("Checking Directory Structure")
    
    required_dirs = [
        '.kiro',
        '.kiro/hooks',
        '.kiro/steering',
        '.kiro/settings',
        '.kiro/specs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print_success(f"Directory exists: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def check_agent_hooks() -> Dict[str, Any]:
    """Check Agent Hooks configuration."""
    print_header("Checking Agent Hooks")
    
    hooks_dir = Path('.kiro/hooks')
    if not hooks_dir.exists():
        print_error("Hooks directory not found")
        return {'total': 0, 'enabled': 0, 'disabled': 0, 'errors': 0}
    
    hook_files = list(hooks_dir.glob('*.json'))
    stats = {'total': 0, 'enabled': 0, 'disabled': 0, 'errors': 0}
    
    for hook_file in hook_files:
        stats['total'] += 1
        try:
            with open(hook_file, 'r') as f:
                hook_data = json.load(f)
            
            name = hook_data.get('name', hook_file.stem)
            enabled = hook_data.get('enabled', False)
            trigger_type = hook_data.get('trigger', {}).get('type', 'unknown')
            
            if enabled:
                stats['enabled'] += 1
                print_success(f"{name} - Enabled ({trigger_type})")
            else:
                stats['disabled'] += 1
                print_warning(f"{name} - Disabled ({trigger_type})")
            
            # Validate structure
            if 'trigger' not in hook_data:
                print_error(f"  Missing 'trigger' field")
                stats['errors'] += 1
            if 'action' not in hook_data:
                print_error(f"  Missing 'action' field")
                stats['errors'] += 1
                
        except json.JSONDecodeError as e:
            print_error(f"{hook_file.name} - Invalid JSON: {e}")
            stats['errors'] += 1
        except Exception as e:
            print_error(f"{hook_file.name} - Error: {e}")
            stats['errors'] += 1
    
    print_info(f"\nSummary: {stats['total']} hooks ({stats['enabled']} enabled, {stats['disabled']} disabled, {stats['errors']} errors)")
    return stats

def check_steering_docs() -> Dict[str, Any]:
    """Check Steering Documents configuration."""
    print_header("Checking Steering Documents")
    
    steering_dir = Path('.kiro/steering')
    if not steering_dir.exists():
        print_error("Steering directory not found")
        return {'total': 0, 'always': 0, 'conditional': 0, 'errors': 0}
    
    steering_files = list(steering_dir.glob('*.md'))
    stats = {'total': 0, 'always': 0, 'conditional': 0, 'manual': 0, 'errors': 0}
    
    for steering_file in steering_files:
        stats['total'] += 1
        try:
            with open(steering_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for frontmatter
            if content.startswith('---'):
                frontmatter_end = content.find('---', 3)
                if frontmatter_end > 0:
                    frontmatter = content[3:frontmatter_end]
                    
                    if 'inclusion: always' in frontmatter:
                        stats['always'] += 1
                        print_success(f"{steering_file.name} - Always included")
                    elif 'inclusion: fileMatch' in frontmatter:
                        stats['conditional'] += 1
                        # Extract pattern
                        for line in frontmatter.split('\n'):
                            if 'fileMatchPattern' in line:
                                pattern = line.split(':', 1)[1].strip().strip('"\'')
                                print_success(f"{steering_file.name} - Conditional (pattern: {pattern})")
                                break
                        else:
                            print_warning(f"{steering_file.name} - Conditional (no pattern found)")
                    elif 'inclusion: manual' in frontmatter:
                        stats['manual'] += 1
                        print_success(f"{steering_file.name} - Manual inclusion")
                    else:
                        print_warning(f"{steering_file.name} - Unknown inclusion type")
                        stats['errors'] += 1
                else:
                    print_error(f"{steering_file.name} - Invalid frontmatter (no closing ---)")
                    stats['errors'] += 1
            else:
                print_warning(f"{steering_file.name} - No frontmatter (will not be loaded)")
                stats['errors'] += 1
                
        except Exception as e:
            print_error(f"{steering_file.name} - Error: {e}")
            stats['errors'] += 1
    
    print_info(f"\nSummary: {stats['total']} docs ({stats['always']} always, {stats['conditional']} conditional, {stats['manual']} manual, {stats['errors']} errors)")
    return stats

def check_mcp_config() -> Dict[str, Any]:
    """Check MCP configuration."""
    print_header("Checking MCP Configuration")
    
    mcp_config_path = Path('.kiro/settings/mcp.json')
    if not mcp_config_path.exists():
        print_error("MCP configuration file not found")
        return {'total': 0, 'enabled': 0, 'disabled': 0, 'errors': 0}
    
    try:
        with open(mcp_config_path, 'r') as f:
            mcp_config = json.load(f)
        
        servers = mcp_config.get('mcpServers', {})
        stats = {'total': len(servers), 'enabled': 0, 'disabled': 0, 'errors': 0}
        
        for server_name, server_config in servers.items():
            disabled = server_config.get('disabled', False)
            command = server_config.get('command', 'unknown')
            auto_approve = server_config.get('autoApprove', [])
            
            if disabled:
                stats['disabled'] += 1
                print_warning(f"{server_name} - Disabled")
            else:
                stats['enabled'] += 1
                print_success(f"{server_name} - Enabled (command: {command})")
                if auto_approve:
                    print_info(f"  Auto-approved tools: {', '.join(auto_approve)}")
            
            # Validate structure
            if 'command' not in server_config:
                print_error(f"  Missing 'command' field")
                stats['errors'] += 1
            if 'args' not in server_config:
                print_warning(f"  Missing 'args' field")
        
        print_info(f"\nSummary: {stats['total']} servers ({stats['enabled']} enabled, {stats['disabled']} disabled, {stats['errors']} errors)")
        return stats
        
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in MCP config: {e}")
        return {'total': 0, 'enabled': 0, 'disabled': 0, 'errors': 1}
    except Exception as e:
        print_error(f"Error reading MCP config: {e}")
        return {'total': 0, 'enabled': 0, 'disabled': 0, 'errors': 1}

def check_uv_installation():
    """Check if uv is installed for MCP servers."""
    print_header("Checking MCP Dependencies")
    
    import subprocess
    
    try:
        result = subprocess.run(['uv', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"uv is installed: {version}")
            return True
        else:
            print_error("uv command failed")
            return False
    except FileNotFoundError:
        print_error("uv is not installed")
        print_info("Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    except Exception as e:
        print_warning(f"Could not check uv installation: {e}")
        return False

def check_environment():
    """Check environment variables."""
    print_header("Checking Environment Variables")
    
    env_vars = {
        'OPENAI_API_KEY': 'Required for LLM analysis',
        'GITHUB_TOKEN': 'Optional - for GitHub MCP server'
    }
    
    for var_name, description in env_vars.items():
        if os.getenv(var_name):
            print_success(f"{var_name} is set - {description}")
        else:
            if 'Optional' in description:
                print_warning(f"{var_name} not set - {description}")
            else:
                print_error(f"{var_name} not set - {description}")

def generate_report(results: Dict[str, Any]):
    """Generate final diagnostic report."""
    print_header("Diagnostic Report")
    
    total_issues = 0
    
    # Count issues
    if results.get('hooks'):
        total_issues += results['hooks'].get('errors', 0)
    if results.get('steering'):
        total_issues += results['steering'].get('errors', 0)
    if results.get('mcp'):
        total_issues += results['mcp'].get('errors', 0)
    
    if total_issues == 0:
        print_success("All checks passed! Your Kiro setup looks good.")
    else:
        print_warning(f"Found {total_issues} issue(s) that need attention.")
    
    print_info("\nNext steps:")
    print("  1. Review any errors or warnings above")
    print("  2. Check .kiro/TESTING_GUIDE.md for detailed testing instructions")
    print("  3. Enable hooks you want to use in .kiro/hooks/*.json")
    print("  4. Install uv if you want to use MCP servers")
    print("  5. Test features in Kiro IDE")

def main():
    """Run all diagnostic checks."""
    print(f"\n{BOLD}Kiro Features Diagnostic Tool{RESET}")
    print("This script checks your Kiro configuration for issues.\n")
    
    results = {}
    
    # Run checks
    check_directory_structure()
    results['hooks'] = check_agent_hooks()
    results['steering'] = check_steering_docs()
    results['mcp'] = check_mcp_config()
    results['uv_installed'] = check_uv_installation()
    check_environment()
    
    # Generate report
    generate_report(results)
    
    print(f"\n{BOLD}Diagnostic complete!{RESET}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Diagnostic interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{RED}Unexpected error: {e}{RESET}")
        sys.exit(1)
