#!/usr/bin/env python3
"""
OSV Vulnerability MCP Server for Kiro.

This MCP server provides tools for querying the OSV (Open Source Vulnerabilities)
database for security vulnerabilities in npm and PyPI packages.

Features:
- Single package vulnerability lookup
- Batch vulnerability queries (parallel)
- Ecosystem support: npm, PyPI

Usage:
    Run as MCP server: python tools/osv_mcp_server.py
"""

import asyncio
import aiohttp
import json
from typing import Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("osv-vulnerability-scanner")

# OSV API configuration
OSV_API_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
MAX_CONCURRENT = 10
REQUEST_TIMEOUT = 15


async def query_osv_single(
    session: aiohttp.ClientSession,
    package_name: str,
    ecosystem: str,
    version: str | None = None
) -> dict[str, Any]:
    """Query OSV API for a single package."""
    query = {"package": {"name": package_name, "ecosystem": ecosystem}}
    if version:
        query["version"] = version
    
    try:
        async with session.post(
            OSV_API_URL,
            json=query,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        ) as response:
            if response.status == 200:
                data = await response.json()
                vulns = data.get("vulns", [])
                return {
                    "package": package_name,
                    "ecosystem": ecosystem,
                    "version": version,
                    "vulnerabilities": [
                        {
                            "id": v.get("id"),
                            "summary": v.get("summary", "No summary"),
                            "severity": _extract_severity(v),
                            "fixed_versions": _extract_fixed_versions(v)
                        }
                        for v in vulns
                    ],
                    "vulnerability_count": len(vulns),
                    "success": True
                }
            else:
                return {
                    "package": package_name,
                    "ecosystem": ecosystem,
                    "vulnerabilities": [],
                    "vulnerability_count": 0,
                    "success": response.status == 404,
                    "error": None if response.status == 404 else f"HTTP {response.status}"
                }
    except Exception as e:
        return {
            "package": package_name,
            "ecosystem": ecosystem,
            "vulnerabilities": [],
            "vulnerability_count": 0,
            "success": False,
            "error": str(e)
        }


def _extract_severity(vuln: dict) -> str:
    """Extract severity from vulnerability data."""
    severity = vuln.get("database_specific", {}).get("severity", "")
    if severity:
        return severity
    
    # Try CVSS score
    for severity_item in vuln.get("severity", []):
        if severity_item.get("type") == "CVSS_V3":
            score = float(severity_item.get("score", "0").split("/")[0])
            if score >= 9.0:
                return "CRITICAL"
            elif score >= 7.0:
                return "HIGH"
            elif score >= 4.0:
                return "MEDIUM"
            else:
                return "LOW"
    return "UNKNOWN"


def _extract_fixed_versions(vuln: dict) -> list[str]:
    """Extract fixed versions from vulnerability data."""
    fixed = []
    for affected in vuln.get("affected", []):
        for range_item in affected.get("ranges", []):
            for event in range_item.get("events", []):
                if "fixed" in event:
                    fixed.append(event["fixed"])
    return fixed


@mcp.tool()
async def check_package_vulnerabilities(
    package_name: str,
    ecosystem: str,
    version: str = ""
) -> str:
    """
    Check a single package for known vulnerabilities in the OSV database.
    
    Args:
        package_name: Name of the package (e.g., "requests", "lodash")
        ecosystem: Package ecosystem - "PyPI" for Python, "npm" for JavaScript
        version: Optional specific version to check (e.g., "2.6.0")
    
    Returns:
        JSON string with vulnerability information
    """
    async with aiohttp.ClientSession() as session:
        result = await query_osv_single(
            session,
            package_name,
            ecosystem,
            version if version else None
        )
    return json.dumps(result, indent=2)


@mcp.tool()
async def check_multiple_packages(packages_json: str) -> str:
    """
    Check multiple packages for vulnerabilities in parallel.
    
    Args:
        packages_json: JSON array of packages, each with "name", "ecosystem", and optional "version"
                      Example: [{"name": "requests", "ecosystem": "PyPI", "version": "2.6.0"}]
    
    Returns:
        JSON string with vulnerability results for all packages
    """
    try:
        packages = json.loads(packages_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})
    
    if not isinstance(packages, list):
        return json.dumps({"error": "Input must be a JSON array"})
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for parallel execution
        tasks = [
            query_osv_single(
                session,
                pkg.get("name", ""),
                pkg.get("ecosystem", "PyPI"),
                pkg.get("version")
            )
            for pkg in packages
        ]
        
        # Execute with concurrency limit
        results = []
        for i in range(0, len(tasks), MAX_CONCURRENT):
            batch = tasks[i:i + MAX_CONCURRENT]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({"error": str(result), "success": False})
                else:
                    results.append(result)
    
    # Summary
    total_vulns = sum(r.get("vulnerability_count", 0) for r in results)
    successful = sum(1 for r in results if r.get("success", False))
    
    return json.dumps({
        "summary": {
            "packages_checked": len(packages),
            "successful_queries": successful,
            "total_vulnerabilities": total_vulns
        },
        "results": results
    }, indent=2)


@mcp.tool()
async def get_vulnerability_details(vuln_id: str) -> str:
    """
    Get detailed information about a specific vulnerability by ID.
    
    Args:
        vuln_id: The vulnerability ID (e.g., "GHSA-x84v-xcm2-53pg", "CVE-2023-1234")
    
    Returns:
        JSON string with detailed vulnerability information
    """
    url = f"https://api.osv.dev/v1/vulns/{vuln_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return json.dumps({
                        "id": data.get("id"),
                        "summary": data.get("summary"),
                        "details": data.get("details"),
                        "severity": _extract_severity(data),
                        "references": [ref.get("url") for ref in data.get("references", [])],
                        "affected_packages": [
                            {
                                "ecosystem": aff.get("package", {}).get("ecosystem"),
                                "name": aff.get("package", {}).get("name"),
                                "versions": aff.get("versions", [])
                            }
                            for aff in data.get("affected", [])
                        ],
                        "success": True
                    }, indent=2)
                else:
                    return json.dumps({
                        "error": f"Vulnerability not found: HTTP {response.status}",
                        "success": False
                    })
        except Exception as e:
            return json.dumps({"error": str(e), "success": False})


if __name__ == "__main__":
    mcp.run()
