# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""Licensing summarizer for must-gather.

This module generates markdown reports from collected licensing data,
providing a comprehensive view of license entitlements, token usage,
and compliance status.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def _formatTimestamp(timestamp: str) -> str:
    """Format timestamp to human-readable format.

    Args:
        timestamp (str): ISO 8601 timestamp string

    Returns:
        str: Formatted timestamp (date only if time is 00:00:00)
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # If time is midnight (00:00:00), only show date
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return timestamp


def _formatBytes(bytes_value: int) -> str:
    """Format bytes to human-readable size.

    Args:
        bytes_value (int): Size in bytes

    Returns:
        str: Formatted size string (e.g., "1.5 GB")
    """
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_value / (1024 ** 3):.2f} GB"


def _loadJsonFile(filePath: str, maxSizeMb: int = 5) -> Optional[Dict[str, Any]]:
    """Load JSON data from file with size limit.

    Args:
        filePath (str): Path to JSON file
        maxSizeMb (int): Maximum file size in MB. Defaults to 5MB.

    Returns:
        dict: Parsed JSON data, or None if file doesn't exist, is too large, or is invalid
    """
    if not os.path.exists(filePath):
        return None

    try:
        # Check file size before loading
        fileSize = os.path.getsize(filePath)
        maxSize = maxSizeMb * 1024 * 1024

        if fileSize > maxSize:
            logger.warning(f"Skipping {filePath}: file too large ({fileSize / 1024 / 1024:.1f}MB > {maxSizeMb}MB)")
            return None

        with open(filePath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {filePath}: {e}")
        return None


def _generateTokensSection(data: Optional[Dict[str, Any]]) -> str:
    """Generate tokens section.

    Args:
        data (dict): Tokens data (single token object, not a list)

    Returns:
        str: Markdown formatted section
    """
    if not data:
        return "**Status:** No token data available\n\n"

    lines = ["## Current Pool\n\n"]

    # Token summary as table
    tokenId = data.get("tokenId", "N/A")
    entitled = data.get("entitled", 0)
    used = data.get("used", 0)
    available = data.get("available", 0)
    reserved = data.get("reserved", 0)
    concurrent = data.get("concurrent", 0)
    expirationDate = _formatTimestamp(data.get("expirationDate", ""))

    # Get issued date from first entitlement
    entitlements = data.get("entitlements", [])
    issuedDate = "N/A"
    if entitlements and len(entitlements) > 0:
        issuedDate = _formatTimestamp(entitlements[0].get("issuedDate", ""))

    lines.append("| Metric | Value |\n")
    lines.append("|--------|-------|\n")
    lines.append(f"| Token ID | {tokenId} |\n")
    lines.append(f"| Entitled | {entitled} |\n")
    lines.append(f"| Used | {used} |\n")
    lines.append(f"| Available | {available} |\n")
    lines.append(f"| Reserved | {reserved} |\n")
    lines.append(f"| Concurrent | {concurrent} |\n")
    lines.append(f"| Issued Date | {issuedDate} |\n")
    lines.append(f"| Expiration Date | {expirationDate} |\n\n")

    # Products
    products = data.get("products", [])
    if products:
        lines.append("### Current Usage\n\n")
        lines.append("| Product ID | Version | Used |\n")
        lines.append("|------------|---------|------|\n")
        for prod in products:
            productId = prod.get("productId", "N/A")
            version = prod.get("productVersion", "N/A")
            used = prod.get("used", 0)
            lines.append(f"| {productId} | {version} | {used} |\n")
        lines.append("\n")

    return "".join(lines)


def _generateConfigSection(data: Optional[Dict[str, Any]]) -> str:
    """Generate configuration section.

    Args:
        data (dict): Configuration data

    Returns:
        str: Markdown formatted section
    """
    if not data:
        return "**Status:** No configuration data available\n\n"

    lines = ["## License Configuration\n\n"]
    lines.append("| Setting | Value |\n")
    lines.append("|---------|-------|\n")

    # Auth enforcement
    auth = data.get("auth", {})
    authEnforce = "✅ Enabled" if auth.get("enforce", False) else "⚠️ Disabled"
    lines.append(f"| Auth Enforcement | {authEnforce} |\n")

    # Compliance enforcement
    compliance = data.get("compliance", {})
    complianceEnforce = "✅ Enabled" if compliance.get("enforce", False) else "⚠️ Disabled"
    lines.append(f"| Compliance Enforcement | {complianceEnforce} |\n")

    # Registration
    registration = data.get("registration", {})
    registrationOpen = "✅ Open" if registration.get("open", False) else "🔒 Closed"
    lines.append(f"| Registration | {registrationOpen} |\n")

    # Reporting settings
    reporting = data.get("reporting", {})
    if reporting:
        lines.append(f"| Max Daily Reports | {reporting.get('maxDailyReports', 'N/A')} |\n")
        lines.append(f"| Max Hourly Reports | {reporting.get('maxHourlyReports', 'N/A')} |\n")
        lines.append(f"| Max Monthly Reports | {reporting.get('maxMonthlyReports', 'N/A')} |\n")
        lines.append(f"| Report Generation Period | {reporting.get('reportGenerationPeriod', 'N/A')}s |\n")
        lines.append(f"| Sampling Period | {reporting.get('samplingPeriod', 'N/A')}s |\n")

    lines.append("\n")
    return "".join(lines)


def _generateTokenUsageSection(data: Optional[Any]) -> tuple:
    """Generate token usage report section and return dates used.

    Args:
        data: Token usage report data (list of daily usage records)

    Returns:
        tuple: (Markdown formatted section, list of dates used)
    """
    if not data:
        return "**Status:** No token-usage data available\n\n", []

    lines = ["## Token Usage History\n"]

    # Data is a list of records
    if not isinstance(data, list) or len(data) == 0:
        lines.append("**Status:** No usage data available\n\n")
        return "".join(lines), []

    # Take last 10 records (most recent)
    recentRecords = data[-10:] if len(data) >= 10 else data
    recentRecords.reverse()  # Show newest first

    # Extract dates for license usage filtering
    usedDates = [record.get("date", "") for record in recentRecords]

    lines.append("### Last 10 Reports\n\n")
    lines.append("| Date | Token ID | Period | Concurrent | Reserved | Used | Entitled |\n")
    lines.append("|------|----------|--------|------------|----------|------|----------|\n")

    for record in recentRecords:
        date = record.get("date", "")
        formattedDate = _formatTimestamp(date)
        tokenId = record.get("tokenId", "N/A")
        period = record.get("period", "N/A")
        stats = record.get("stats", {})

        concurrent = stats.get("concurrent", {}).get("average", 0) if stats else 0
        reserved = stats.get("reserved", {}).get("average", 0) if stats else 0
        used = stats.get("used", {}).get("average", 0) if stats else 0
        entitled = stats.get("entitled", {}).get("average", 0) if stats else 0

        lines.append(f"| {formattedDate} | {tokenId} | {period} | {concurrent} | {reserved} | {used} | {entitled} |\n")

    lines.append("\n")
    return "".join(lines), usedDates


def _generateLicenseUsageSection(data: Optional[Any], filterDates: list[str]) -> str:
    """Generate license usage report section filtered by dates.

    Args:
        data: License usage report data (list of daily usage records)
        filterDates: List of dates to include (from token usage)

    Returns:
        str: Markdown formatted section
    """
    if not data:
        return "**Status:** No license-usage data available\n\n"

    lines = ["## License Usage History\n"]

    # Data is a list of records
    if not isinstance(data, list) or len(data) == 0:
        lines.append("**Status:** No usage data available\n\n")
        return "".join(lines)

    # Filter records by dates from token usage
    filteredRecords = [r for r in data if r.get("date", "") in filterDates]

    if not filteredRecords:
        lines.append("**Status:** No usage data available for selected dates\n\n")
        return "".join(lines)

    # Group by date
    dateGroups = {}
    for record in filteredRecords:
        date = record.get("date", "")
        if date not in dateGroups:
            dateGroups[date] = []
        dateGroups[date].append(record)

    # Sort dates to match token usage order (newest first)
    sortedDates = sorted(dateGroups.keys(), reverse=True)

    lines.append("### Last 10 Reports\n\n")

    for date in sortedDates:
        records = dateGroups[date]
        formattedDate = _formatTimestamp(date)

        lines.append(f"#### {formattedDate}\n\n")
        lines.append("| Product ID | Period | Cost | Count |\n")
        lines.append("|------------|--------|------|-------|\n")

        for record in records:
            productId = record.get("productId", "N/A")
            period = record.get("period", "N/A")
            stats = record.get("stats", {})

            avgCost = stats.get("cost", {}).get("average", 0) if stats else 0
            avgCount = stats.get("count", {}).get("average", 0) if stats else 0

            # Skip licenses with zero usage
            if avgCost == 0 and avgCount == 0:
                continue

            lines.append(f"| {productId} | {period} | {avgCost} | {avgCount} |\n")

        lines.append("\n")

    lines.append("\n")
    return "".join(lines)


def summarize(outputDir: str) -> bool:
    """Generate licensing summary for all MAS instances.

    Creates licensing summary markdown files at licensing/{instance}/_summary.md
    for each instance with collected licensing data.

    Args:
        outputDir (str): Base output directory for must-gather

    Returns:
        bool: True if summary generation succeeded, False otherwise
    """
    licensingDir = os.path.join(outputDir, "licensing")

    if not os.path.exists(licensingDir):
        logger.info("No licensing data found - skipping licensing summary")
        return True

    # Find all instance directories
    instances = [d for d in os.listdir(licensingDir) if os.path.isdir(os.path.join(licensingDir, d))]

    if not instances:
        logger.info("No licensing instances found - skipping licensing summary")
        return True

    logger.info(f"Generating licensing summaries for {len(instances)} instance(s)")

    # Create summaries directory
    summariesDir = os.path.join(outputDir, "summaries")
    os.makedirs(summariesDir, exist_ok=True)

    for instanceId in instances:
        instanceDir = os.path.join(licensingDir, instanceId)
        summaryPath = os.path.join(summariesDir, f"mas-{instanceId}-licensing.md")

        try:
            logger.debug(f"Loading data files for {instanceId}")

            # Load all data files (all are optional, may not exist if API calls failed)
            tokensData = _loadJsonFile(os.path.join(instanceDir, "tokens.json"))
            logger.debug("Loaded tokens.json")

            configData = _loadJsonFile(os.path.join(instanceDir, "config.json"))
            logger.debug("Loaded config.json")

            # Load reports with increased size limit for license-usage
            licenseUsageData = _loadJsonFile(os.path.join(instanceDir, "license-usage.json"), maxSizeMb=10)
            tokenUsageData = _loadJsonFile(os.path.join(instanceDir, "token-usage.json"), maxSizeMb=2)
            logger.debug("Loaded report files with size limits")

            # Generate summary
            lines = [
                f"# Licensing Summary - {instanceId}\n\n",
                f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n",
                "---\n\n",
            ]

            # Add sections
            lines.append(_generateConfigSection(configData))
            lines.append(_generateTokensSection(tokensData))

            # Add usage reports - token usage first, then license usage filtered by token dates
            if tokenUsageData:
                tokenSection, usedDates = _generateTokenUsageSection(tokenUsageData)
                lines.append(tokenSection)

                # Generate license usage filtered by dates from token usage
                if licenseUsageData and usedDates:
                    lines.append(_generateLicenseUsageSection(licenseUsageData, usedDates))
            elif licenseUsageData:
                # If no token data, show license usage without filtering
                lines.append(_generateLicenseUsageSection(licenseUsageData, []))

            # Write summary
            with open(summaryPath, "w") as f:
                f.write("".join(lines))

            logger.info(f"✅ Generated licensing summary for instance {instanceId}")

        except Exception as e:
            logger.error(f"❌ Failed to generate licensing summary for {instanceId}: {e}")
            continue

    return True
