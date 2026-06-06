# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

"""MAS Quick Summary generator for must-gather.

This module provides functionality to generate quick summary reports for MAS instances
to help troubleshoot user sync issues. It calls the mg-quick-summary-mas script to
generate the summary.
"""

import os
import logging
import subprocess
from kubernetes.dynamic import DynamicClient

logger = logging.getLogger(__name__)


def generateMASQuickSummary(dynClient: DynamicClient, masInstanceId: str, outputDir: str) -> bool:
    """Generate MAS quick summary report for an instance.

    Calls the mg-quick-summary-mas script to generate a quick summary report
    for troubleshooting user sync issues. The report is saved to
    mas-quick-summary/{instance}.txt.

    Args:
        dynClient (DynamicClient): Kubernetes Dynamic Client for API access
        masInstanceId (str): MAS instance ID to generate summary for
        outputDir (str): Base output directory

    Returns:
        bool: True if generation succeeded or script not found, False if critical error occurred
    """
    try:
        # Create quick summary output directory
        quickSummaryDir = os.path.join(outputDir, "mas-quick-summary")
        os.makedirs(quickSummaryDir, exist_ok=True)

        # Output file path
        outputFile = os.path.join(quickSummaryDir, f"{masInstanceId}.txt")

        # Try to call mg-quick-summary-mas script
        summaryScript = "mg-quick-summary-mas"
        try:
            logger.debug(f"Attempting to run quick summary script: {summaryScript}")
            result = subprocess.run(
                [summaryScript, masInstanceId],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                # Write output to file
                with open(outputFile, "w") as f:
                    f.write(result.stdout)
                logger.info(f"Successfully generated quick summary for {masInstanceId}")
            else:
                logger.warning(f"Quick summary script {summaryScript} failed with return code {result.returncode}")
                # Write error to file
                with open(outputFile, "w") as f:
                    f.write(f"Quick summary generation failed:\n{result.stderr}\n")

        except FileNotFoundError:
            logger.debug(f"Quick summary script {summaryScript} not found, skipping")
        except subprocess.TimeoutExpired:
            logger.warning(f"Quick summary script {summaryScript} timed out")
            # Write timeout message to file
            with open(outputFile, "w") as f:
                f.write("Quick summary generation timed out after 300 seconds\n")
        except Exception as e:
            logger.debug(f"Error running quick summary script {summaryScript}: {e}")
            # Write error to file
            with open(outputFile, "w") as f:
                f.write(f"Error generating quick summary: {e}\n")

        return True

    except Exception as e:
        logger.error(f"Failed to generate quick summary for {masInstanceId}: {e}")
        return False
