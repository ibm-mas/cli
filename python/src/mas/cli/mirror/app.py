#!/usr/bin/env python
# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

import base64
import json
import logging
import re
import selectors
import shutil
import subprocess
import yaml
import urllib.request
import urllib.error
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from os import path, environ, makedirs

from alive_progress import alive_bar
from prompt_toolkit import print_formatted_text, HTML

from mas.devops.data import getCatalog, NoSuchCatalogError

from ..cli import BaseApp
from .argParser import mirrorArgParser
from .config import PACKAGE_CONFIGS


logger = logging.getLogger(__name__)

# Constants
EMPTY_PROGRESS_BAR = " |" + " " * 20 + "|"


def logMethodCall(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f">>> MirrorApp.{func.__name__}")
        result = func(self, *args, **kwargs)
        logger.debug(f"<<< MirrorApp.{func.__name__}")
        return result
    return wrapper


@dataclass
class MirrorResult:
    """Result of a mirror operation."""
    images: int
    mirrored: int
    name: str = ""  # Name of the package/catalog being mirrored
    failed_images: List[str] = field(default_factory=list)  # List of failed image URLs

    @property
    def success(self) -> bool:
        """
        Determine if the mirror operation was successful.

        Returns:
            True if all images were mirrored successfully, False otherwise.
        """
        return self.images != 0 and self.images == self.mirrored

    @property
    def failed_count(self) -> int:
        """
        Get the number of failed images.

        Returns:
            Number of images that failed to mirror.
        """
        return max(0, self.images - self.mirrored)


def stripLogPrefix(line: str) -> str:
    """
    Strip timestamp and log level prefix from command output.

    Handles format: "2026/02/02 18:12:25  [INFO]   : {actual message}"
    Removes everything up to and including the first ": " after a log level.

    Args:
        line: The log line to process

    Returns:
        The line with prefix stripped, or original line if no match
    """
    # Check if line starts with a timestamp pattern (with or without ANSI codes)
    # If it does, find the first ": " after a log level and remove everything before it
    if re.match(r'^.*?\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}', line):
        # Find position of ": " after the log level
        # Split on first occurrence of ": " that comes after a bracket
        parts = line.split(': ', 1)
        if len(parts) == 2 and '[' in parts[0]:
            return parts[1]

    return line


def countImagesInConfig(configPath: str) -> int:
    """
    Parse YAML config file and count images in mirror.additionalImages.

    Args:
        configPath: Path to the YAML configuration file

    Returns:
        Number of images to be mirrored, or 0 if parsing fails
    """
    try:
        with open(configPath, 'r') as f:
            config = yaml.safe_load(f)

        additionalImages = config.get('mirror', {}).get('additionalImages', [])
        imageCount = len(additionalImages)
        logger.debug(f"Found {imageCount} images in {configPath}")
        return imageCount
    except FileNotFoundError:
        logger.error(f"Config file not found: {configPath}")
        return 0
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML config {configPath}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error reading config {configPath}: {e}")
        return 0


def getISC(configPath: str) -> str:
    """
    Get the Image Set Config file, downloading from GitHub if it doesn't exist locally.

    The config file is expected to be in ~/.ibm-mas/{configPath}.
    If the file doesn't exist, it will be downloaded from:
    https://github.com/ibm-mas/image-set-configs/blob/master/{configPath}

    Args:
        configPath: Relative path to the config file (e.g., "catalogs/v9-260129-amd64.yaml")

    Returns:
        Full path to the local config file

    Raises:
        FileNotFoundError: If the file doesn't exist and cannot be downloaded
    """
    # Get home directory
    homeDir = environ.get('HOME') or environ.get('USERPROFILE') or ''
    if not homeDir:
        raise FileNotFoundError("Could not determine home directory")

    # Construct full local path with .ibm-mas prefix
    localPath = path.join(homeDir, '.ibm-mas', 'image-set-configs', configPath)

    # If file exists, return it
    if path.exists(localPath):
        logger.info(f"Using existing config file: {localPath}")
        return localPath

    # File doesn't exist, try to download it
    logger.info(f"Config file not found locally: {localPath}")

    # Construct GitHub raw content URL
    # Convert blob URL to raw content URL
    githubUrl = f"https://raw.githubusercontent.com/ibm-mas/image-set-configs/master/{configPath}"

    logger.info(f"Attempting to download from: {githubUrl}")

    try:
        # Create directory if it doesn't exist
        localDir = path.dirname(localPath)
        makedirs(localDir, exist_ok=True)

        # Download the file
        with urllib.request.urlopen(githubUrl) as response:
            content = response.read()

        # Write to local file
        with open(localPath, 'wb') as f:
            f.write(content)

        logger.info(f"Successfully downloaded config file to: {localPath}")
        return localPath

    except urllib.error.HTTPError as e:
        logger.error(f"Failed to download config file from GitHub: HTTP {e.code} - {e.reason}")
        raise FileNotFoundError(f"Config file not found locally and could not be downloaded from GitHub: {configPath}") from e
    except urllib.error.URLError as e:
        logger.error(f"Failed to download config file from GitHub: {e.reason}")
        raise FileNotFoundError(f"Config file not found locally and could not be downloaded from GitHub: {configPath}") from e
    except Exception as e:
        logger.error(f"Unexpected error downloading config file: {e}")
        raise FileNotFoundError(f"Config file not found locally and could not be downloaded from GitHub: {configPath}") from e


def _processStreams(process: subprocess.Popen, resultData: Dict, progressBar=None) -> None:
    """
    Process stdout and stderr streams from a subprocess using selectors.

    Uses non-blocking I/O to efficiently read from both streams without threading.
    Filters output and captures result information.

    Args:
        process: The subprocess.Popen object with stdout and stderr pipes
        resultData: Dictionary to store captured result information
        progressBar: Optional alive-progress bar instance to update on image copy success
    """
    # Ensure streams are available
    if process.stdout is None or process.stderr is None:
        return

    # Compile filter patterns into a single case-insensitive regex for performance
    filterPatterns = [
        "Hello, welcome to oc-mirror",
        "setting up the environment for you...",
        "using digest to pull, but tag only for mirroring"
    ]
    # Escape special regex characters and join with OR operator
    filterRegex = re.compile('|'.join(re.escape(pattern) for pattern in filterPatterns), re.IGNORECASE)

    # Set up selector for non-blocking I/O
    sel = selectors.DefaultSelector()
    sel.register(process.stdout, selectors.EVENT_READ, data='stdout')
    sel.register(process.stderr, selectors.EVENT_READ, data='stderr')

    # Track which streams are still open (store file objects, not selectors)
    streamsOpen = {process.stdout.fileno(), process.stderr.fileno()}

    # Initialize failed_images list in resultData if not present
    if 'failed_images' not in resultData:
        resultData['failed_images'] = []

    while streamsOpen:
        # Wait for data to be available on any stream
        events = sel.select(timeout=0.1)

        for key, _ in events:
            streamType = key.data

            # Get the actual file object from the key
            if streamType == 'stdout':
                stream = process.stdout
            else:
                stream = process.stderr

            if stream is None:
                continue

            line = stream.readline()

            if not line:
                # Stream closed
                streamsOpen.discard(stream.fileno())
                sel.unregister(stream)
                continue

            lineStripped = line.rstrip()

            # Capture result information BEFORE stripping prefix
            # Match both success case: "X / Y additional images mirrored successfully"
            # And partial failure case: "X / Y additional images mirrored: Some additional images failed"
            resultMatch = re.search(r'(\d+)\s+/\s+(\d+)\s+additional images mirrored', lineStripped)
            if resultMatch:
                resultData['mirrored'] = int(resultMatch.group(1))
                resultData['images'] = int(resultMatch.group(2))
                logger.debug(f"Captured result: {resultData['mirrored']}/{resultData['images']}")

            # Detect "Success copying" and update progress bar
            successMatch = re.search(r'Success copying .+ ➡️', lineStripped)
            if successMatch and progressBar is not None:
                progressBar()  # Increment progress bar
                logger.debug("Progress bar incremented")

            # Capture failed image URLs from error messages
            # Pattern matches lines like: "Failed to copy generic gcr.io/kubebuilder/kube-rbac-proxy:1.1.3@sha256:..."
            # The image URL is at the end of the line after "Failed to copy" and optional type (generic, etc.)
            failedImageMatch = re.search(r'Failed to copy\s+(?:\w+\s+)?(.+)$', lineStripped)
            if failedImageMatch:
                imageUrl = failedImageMatch.group(1).strip()
                if imageUrl and imageUrl not in resultData['failed_images']:
                    resultData['failed_images'].append(imageUrl)
                    logger.debug(f"Captured failed image: {imageUrl}")

            # Strip duplicate timestamp/level prefix from command output
            cleanLine = stripLogPrefix(lineStripped)

            # Skip lines matching the filter regex (case-insensitive)
            if not filterRegex.search(lineStripped):
                # Log to appropriate level based on stream
                if streamType == 'stdout':
                    logger.debug(cleanLine)
                else:
                    logger.error(cleanLine)

    sel.close()


def runCommand(cmd: List[str], progressBar=None) -> tuple[int, Dict]:
    """
    Execute a command and stream output/errors in real-time.

    Args:
        cmd: List of command arguments to execute
        progressBar: Optional alive-progress bar instance to update on image copy success

    Returns:
        Tuple of (exitCode, resultData) where resultData contains captured information
    """
    logger.info(f"Executing: {' '.join(cmd)}")

    # Dictionary to capture result data from output
    resultData = {}

    try:
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered for real-time output
        ) as process:
            # Process streams using selectors for efficient non-blocking I/O
            _processStreams(process, resultData, progressBar)

            # Wait for process to complete
            returnCode = process.wait()

            if returnCode != 0:
                logger.error(f"Command failed with exit code {returnCode}")

            return returnCode, resultData

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1, {}


def _executeMirror(configPath: str, displayName: str, workspacePath: str, mode: str,
                   targetRegistry: str = "", ocMirrorPath: str = "oc-mirror",
                   authFilePath: Optional[str] = None, rootDir: str = "",
                   destTlsVerify: bool = True, imageTimeout: str = "20m") -> MirrorResult:
    """
    Execute the mirror operation for a given configuration.

    This is a common function used by both mirrorPackage and mirrorCatalog.

    Args:
        configPath: Path to the YAML configuration file
        displayName: Display name for progress bar (e.g., "ibm-mas v9.0.5 (amd64)" or "catalog v9-260129-amd64")
        workspacePath: Workspace path for the mirror operation (e.g., "package/arch/version" or "catalog/version")
        mode: Mirror mode ("m2m", "m2d", or "d2m")
        targetRegistry: Target registry for m2m and d2m modes
        ocMirrorPath: Path to oc-mirror binary (default: "oc-mirror")
        authFilePath: Path to authentication file (default: ~/.ibm-mas/auth.json)
        rootDir: Root directory for mirror operations (workspace for m2m, disk storage for m2d/d2m)
        destTlsVerify: Verify TLS certificates for destination registry (default: True)
        imageTimeout: Timeout for image operations (default: "20m")

    Returns:
        MirrorResult object with images, mirrored, and success status.
        Returns images=0, mirrored=0, success=False if operation failed or results couldn't be parsed.
    """
    logger.info(f"Using configuration: {configPath}")

    # Set default auth file path if not provided
    if authFilePath is None:
        homeDir = environ.get('HOME') or environ.get('USERPROFILE') or ''
        authFilePath = path.join(homeDir, '.ibm-mas', 'auth.json')

    # Count images in config file
    totalImages = countImagesInConfig(configPath)
    if totalImages == 0:
        logger.error(f"No images found in config or failed to parse: {configPath}")
        print(f"❌ {displayName} - No images found in config")
        return MirrorResult(images=0, mirrored=0, name=displayName)

    logger.info(f"Found {totalImages} images to mirror")

    # Build TLS verify flag
    tlsVerifyFlag = f"--dest-tls-verify={'true' if destTlsVerify else 'false'}"

    if mode == "m2m":
        cmd = [
            ocMirrorPath, "--v2", "--config", configPath, "--authfile", authFilePath,
            "--workspace", f"file://{rootDir}/{workspacePath}",
            tlsVerifyFlag, "--image-timeout", imageTimeout,
            f"docker://{targetRegistry}"
        ]
    elif mode == "m2d":
        cmd = [
            ocMirrorPath, "--v2", "--config", configPath, "--authfile", authFilePath,
            "--image-timeout", imageTimeout,
            f"file://{rootDir}/{workspacePath}",
        ]
    elif mode == "d2m":
        cmd = [
            ocMirrorPath, "--v2", "--config", configPath, "--authfile", authFilePath,
            "--from", f"file://{rootDir}/{workspacePath}",
            tlsVerifyFlag, "--image-timeout", imageTimeout,
            f"docker://{targetRegistry}"
        ]
    else:
        logger.error(f"Unsupported mirror mode: {mode}")
        print(f"❌ {displayName} - Unsupported mirror mode: {mode}")
        return MirrorResult(images=0, mirrored=0, name=displayName)

    # Execute command with progress bar
    # Use fixed-width title (50 chars) for alignment, with in-progress icon
    barTitleBase = displayName.ljust(50)
    barTitle = f"{barTitleBase} ⏳"
    with alive_bar(totalImages, title=barTitle, length=20, enrich_print=False) as bar:
        exitCode, resultData = runCommand(cmd, progressBar=bar)

        # Update bar title with status icon after completion
        if exitCode != 0:
            bar.title = f"{barTitleBase} ❌"
            logger.error(f"Mirror operation failed with exit code {exitCode}")
            # Use mirrored count from resultData if available, otherwise 0
            mirrored = resultData.get('mirrored', 0)
            # Use images count from resultData if available, otherwise totalImages
            images = resultData.get('images', totalImages)
            return MirrorResult(images=images, mirrored=mirrored, name=displayName, failed_images=resultData.get('failed_images', []))

        # Create result object from captured data
        if 'images' in resultData and 'mirrored' in resultData:
            result = MirrorResult(
                images=resultData['images'],
                mirrored=resultData['mirrored'],
                name=displayName,
                failed_images=resultData.get('failed_images', [])
            )
            logger.info(f"Mirror operation completed: {result.mirrored}/{result.images} images mirrored (success={result.success})")

            if result.success:
                bar.title = f"{barTitleBase} ✅"
            else:
                bar.title = f"{barTitleBase} ⚠️"

            return result
        else:
            bar.title = f"{barTitleBase} ⚠️"
            logger.warning("Mirror operation completed but could not parse result statistics")
            # Use mirrored count from resultData if available, otherwise 0
            mirrored = resultData.get('mirrored', 0)
            return MirrorResult(images=totalImages, mirrored=mirrored, name=displayName, failed_images=resultData.get('failed_images', []))


def mirrorPackage(package: str, version: str, arch: str, mode: str,
                  targetRegistry: str = "", flag: bool = True,
                  ocMirrorPath: str = "oc-mirror", authFilePath: Optional[str] = None,
                  rootDir: str = "", destTlsVerify: bool = True,
                  imageTimeout: str = "20m") -> MirrorResult:
    """
    Mirror a package and return the result.

    Args:
        package: Package name (e.g., "ibm-mas")
        version: Package version (e.g., "9.0.5")
        arch: Architecture (e.g., "amd64")
        mode: Mirror mode ("m2m", "m2d", or "d2m")
        targetRegistry: Target registry for m2m and d2m modes
        flag: Whether to actually perform the mirror operation
        ocMirrorPath: Path to oc-mirror binary (default: "oc-mirror")
        authFilePath: Path to authentication file (default: ~/.ibm-mas/auth.json)
        rootDir: Root directory for mirror operations (workspace for m2m, disk storage for m2d/d2m)
        destTlsVerify: Verify TLS certificates for destination registry (default: True)
        imageTimeout: Timeout for image operations (default: "20m")

    Returns:
        MirrorResult object with images, mirrored, and success status.
        Returns images=0, mirrored=0, success=False if operation failed or results couldn't be parsed.
    """
    # Extract major.minor version (first two components)
    versionParts = version.split('.')

    # Validate version format
    if len(versionParts) < 2:
        logger.error(f"Invalid version format: '{version}'. Expected format: 'major.minor.patch' (e.g., '9.0.5')")
        displayName = f"{package} v{version} ({arch})"
        return MirrorResult(images=0, mirrored=0, name=displayName)

    majorMinor = f"{versionParts[0]}.{versionParts[1]}"

    if not flag:
        logger.info(f"Skipping {package} version {version} for {arch} architecture")
        # Add empty progress bar to align with other status messages
        displayName = f"{package} v{version} ({arch})"
        print(f"{displayName.ljust(50)} ⏭️ {EMPTY_PROGRESS_BAR} Mirroring disabled by user")
        return MirrorResult(images=0, mirrored=0, name=displayName)

    logger.info(f"Mirroring {package} version {version} for {arch} architecture")

    # Get or download the config file
    relativeConfigPath = f"packages/{package}/{majorMinor}/{arch}/{package}-{version}-{arch}.yaml"
    try:
        configPath = getISC(relativeConfigPath)
    except FileNotFoundError as e:
        logger.error(f"Failed to get config file: {e}")
        displayName = f"{package} v{version} ({arch})"
        print(f"❌ {displayName} - Config file not found")
        return MirrorResult(images=0, mirrored=0, name=displayName)

    displayName = f"{package} v{version} ({arch})"
    workspacePath = f"{package}/{arch}/{version}"

    return _executeMirror(configPath, displayName, workspacePath, mode, targetRegistry,
                          ocMirrorPath, authFilePath, rootDir, destTlsVerify, imageTimeout)


def mirrorCatalog(version: str, mode: str, targetRegistry: str = "",
                  ocMirrorPath: str = "oc-mirror", authFilePath: Optional[str] = None,
                  rootDir: str = "", destTlsVerify: bool = True,
                  imageTimeout: str = "20m") -> MirrorResult:
    """
    Mirror a catalog and return the result.

    Args:
        version: Catalog version (e.g., "v9-260129-amd64")
        mode: Mirror mode ("m2m", "m2d", or "d2m")
        targetRegistry: Target registry for m2m and d2m modes
        ocMirrorPath: Path to oc-mirror binary (default: "oc-mirror")
        authFilePath: Path to authentication file (default: ~/.ibm-mas/auth.json)
        rootDir: Root directory for mirror operations (workspace for m2m, disk storage for m2d/d2m)
        destTlsVerify: Verify TLS certificates for destination registry (default: True)
        imageTimeout: Timeout for image operations (default: "20m")

    Returns:
        MirrorResult object with images, mirrored, and success status.
        Returns images=0, mirrored=0, success=False if operation failed or results couldn't be parsed.

    Raises:
        ValueError: If catalog version is less than 260129 (January 2026)
    """
    logger.info(f"Mirroring catalog {version}")

    # Validate catalog version - extract date portion (e.g., "260129" from "v9-260129-amd64")
    # Expected format: v{major}-{YYMMDD}-{arch}
    versionMatch = re.match(r'v\d+-(\d{6})-\w+', version)
    if versionMatch:
        catalogDate = int(versionMatch.group(1))
        if catalogDate < 260129:
            raise ValueError(
                f"Mirroring using ImageSetConfigurations is only supported from the January 2026 catalog update onwards. "
                f"Catalog version {version} (date: {catalogDate}) is not supported."
            )
    else:
        logger.warning(f"Could not parse catalog version format: {version}. Skipping version validation.")

    # Get or download the config file
    relativeConfigPath = f"catalogs/{version}.yaml"
    try:
        configPath = getISC(relativeConfigPath)
    except FileNotFoundError as e:
        logger.error(f"Failed to get config file: {e}")
        # Catalog config not found is a fatal error - re-raise with a clear message
        raise FileNotFoundError(f"Unable to locate ImageSetConfiguration for the {version} operator catalog") from e

    displayName = f"catalog {version}"
    workspacePath = f"catalog/{version}"

    return _executeMirror(configPath, displayName, workspacePath, mode, targetRegistry,
                          ocMirrorPath, authFilePath, rootDir, destTlsVerify, imageTimeout)


def validateEnvironmentVariables(mode: str, targetRegistry: str) -> None:
    """
    Validate that required environment variables are set based on the mirror mode.

    Args:
        mode: Mirror mode ("m2m", "m2d", or "d2m")
        targetRegistry: Target registry for m2m and d2m modes

    Raises:
        ValueError: If required environment variables are not set
    """
    missingVars = []

    # Check for target registry credentials (m2m or d2m)
    if mode in ["m2m", "d2m"]:
        if not environ.get('REGISTRY_USERNAME'):
            missingVars.append('REGISTRY_USERNAME')
        if not environ.get('REGISTRY_PASSWORD'):
            missingVars.append('REGISTRY_PASSWORD')

    # Check for IBM Entitlement Key (m2m or m2d)
    if mode in ["m2m", "m2d"]:
        if not environ.get('IBM_ENTITLEMENT_KEY'):
            missingVars.append('IBM_ENTITLEMENT_KEY')

    if missingVars:
        raise ValueError(f"Missing required environment variables: {', '.join(missingVars)}")


def generateAuthFile(mode: str, targetRegistry: str) -> str:
    """
    Generate an authentication file from environment variables.

    Args:
        mode: Mirror mode ("m2m", "m2d", or "d2m")
        targetRegistry: Target registry for m2m and d2m modes

    Returns:
        Path to the generated auth file

    Raises:
        ValueError: If required environment variables are not set
    """
    # Validate environment variables first
    validateEnvironmentVariables(mode, targetRegistry)

    # Get home directory
    homeDir = environ.get('HOME') or environ.get('USERPROFILE') or ''
    if not homeDir:
        raise ValueError("Could not determine home directory")

    # Create auth file path
    authFilePath = path.join(homeDir, '.ibm-mas', 'auth.json')
    authDir = path.dirname(authFilePath)

    # Create directory if it doesn't exist
    makedirs(authDir, exist_ok=True)

    # Build auth configuration
    authConfig = {}

    # Add target registry credentials (m2m or d2m)
    if mode in ["m2m", "d2m"]:
        registryUsername = environ.get('REGISTRY_USERNAME', '')
        registryPassword = environ.get('REGISTRY_PASSWORD', '')
        authString = f"{registryUsername}:{registryPassword}"
        authBase64 = base64.b64encode(authString.encode()).decode()
        authConfig[targetRegistry] = {
            "auth": authBase64
        }

    # Add IBM Entitlement Key (m2m or m2d)
    if mode in ["m2m", "m2d"]:
        ibmEntitlementKey = environ.get('IBM_ENTITLEMENT_KEY', '')
        authString = f"cp:{ibmEntitlementKey}"
        authBase64 = base64.b64encode(authString.encode()).decode()
        authConfig["cp.icr.io/cp"] = {
            "auth": authBase64
        }

    auths = {
        "auths": authConfig
    }

    # Write auth file
    with open(authFilePath, 'w') as f:
        json.dump(auths, f, indent=2)

    logger.info(f"Generated auth file: {authFilePath}")
    return authFilePath


class MirrorApp(BaseApp):

    @logMethodCall
    def interactiveMode(self, simplified: bool, advanced: bool) -> None:
        # Interactive mode
        self._interactiveMode = True

    @logMethodCall
    def nonInteractiveMode(self) -> None:
        self._interactiveMode = False

    @logMethodCall
    def mirror(self, argv):
        """
        Main mirror function that orchestrates the mirroring of catalogs and packages.

        Args:
            argv: Command line arguments
        """
        args = mirrorArgParser.parse_args(args=argv)

        catalogVersion = args.catalog
        release = args.release
        mode = args.mode
        targetRegistry = args.target_registry or ""
        authFile = args.authfile
        rootDir = args.dir
        destTlsVerify = args.dest_tls_verify
        imageTimeout = args.image_timeout
        mirrorAll = args.all

        # Validate that oc-mirror is available on PATH
        if not shutil.which("oc-mirror"):
            logger.error("oc-mirror executable not found on PATH")
            self.fatalError("oc-mirror executable not found on PATH. Please install oc-mirror and ensure it is available in your PATH.")
            return

        # Validate that --target-registry is provided for m2m and d2m modes
        if mode in ["m2m", "d2m"] and not targetRegistry:
            logger.error(f"--target-registry is required when mode is '{mode}'")
            self.fatalError(f"--target-registry is required when mode is '{mode}'")
            return

        # Handle authfile parameter
        if authFile:
            # Validate that the file exists
            if not path.exists(authFile):
                logger.error(f"Auth file does not exist: {authFile}")
                self.fatalError(f"Auth file does not exist: {authFile}")
                return
            logger.info(f"Using provided auth file: {authFile}")
            authFilePath = authFile
        else:
            # Generate auth file from environment variables
            try:
                authFilePath = generateAuthFile(mode, targetRegistry)
            except ValueError as e:
                logger.error(f"Failed to generate auth file: {e}")
                self.fatalError(f"Failed to generate auth file: {e}")
                return

        # First, check if the catalog exists
        try:
            catalog = getCatalog(catalogVersion)
        except NoSuchCatalogError as e:
            logger.error(f"Catalog not found: {e}")
            self.fatalError(f"Catalog {catalogVersion} is not known. Please select a valid IBM Maximo Operator Catalog.")
            return

        # Now validate catalog version (only for valid catalogs)
        # Expected format: v{major}-{YYMMDD}-{arch}
        versionMatch = re.match(r'v\d+-(\d{6})-\w+', catalogVersion)
        if versionMatch:
            catalogDate = int(versionMatch.group(1))
            if catalogDate < 260129:
                self.fatalError(
                    f"Mirroring using ImageSetConfigurations is only supported from the January 2026 catalog update onwards. "
                    f"This function does not support catalog version {catalogVersion}."
                )
                return

        arch = catalogVersion.split("-")[-1]

        self.printH1("Mirror Configuration")
        self.printSummary("Catalog", catalogVersion)
        self.printSummary("Architecture", arch)
        self.printSummary("Release", release)
        self.printSummary("Mode", mode)
        self.printSummary("Authentication File", authFilePath)

        self.printH1("Mirror Target")
        if mode == "m2d":
            self.printSummary("Destination", rootDir)
        else:
            self.printSummary("Destination", targetRegistry)
            self.printSummary("Verify Registry Certificate", destTlsVerify)
        self.printSummary("Mirror Image Timeout", imageTimeout)

        # Track mirror results
        failedMirrors = []  # List of MirrorResult objects that failed
        totalImages = 0
        mirroredImages = 0

        self.printH1("IBM Maximo Operator Catalog")
        try:
            catalogResult = mirrorCatalog(
                version=catalogVersion,
                mode=mode,
                targetRegistry=targetRegistry,
                authFilePath=authFilePath,
                rootDir=rootDir,
                destTlsVerify=destTlsVerify,
                imageTimeout=imageTimeout
            )

            # Track catalog results
            totalImages += catalogResult.images
            mirroredImages += catalogResult.mirrored
            if not catalogResult.success:
                failedMirrors.append(catalogResult)
        except FileNotFoundError as e:
            # Catalog config not found is a fatal error
            print_formatted_text(HTML("\n<B>⚠️  Mirror operation failed</B>"))
            print_formatted_text(HTML(f"<ansired>{e}</ansired>"))
            return

        # Mirror each package with common parameters using shared configuration
        currentGroup = None
        for group, argName, packageName, catalogKey in PACKAGE_CONFIGS:
            # Print section header when group changes
            if group != currentGroup:
                self.printH1(group)
                currentGroup = group

            # Get version from catalog - handle both direct keys and release-specific keys
            perReleaseVersions = [
                "aiservice_version",
                "mas_core_version",
                "mas_assist_version",
                "mas_iot_version",
                "mas_facilities_version",
                "mas_manage_version",
                "mas_monitor_version",
                "mas_predict_version",
                "mas_optimizer_version",
                "mas_visualinspection_version"
            ]
            if catalogKey in perReleaseVersions:
                # Check if the catalogKey exists in the catalog first
                if catalogKey not in catalog or release not in catalog[catalogKey] or (release == "8.10.x" and packageName == "ibm-mas-manage-icd"):
                    logger.info(f"No content available for {packageName} in MAS release {release}")
                    displayName = f"{packageName} ({arch})"
                    print(f"{displayName.ljust(50)} ⏭️ {EMPTY_PROGRESS_BAR} No content to mirror for MAS release {release}")
                    continue

                version = catalog[catalogKey][release]
            else:
                version = catalog[catalogKey]

            # Check if version is empty or None (content exists in catalog but is empty)
            if not version:
                logger.info(f"No content available for {packageName} in MAS release {release}")
                displayName = f"{packageName} ({arch})"
                print(f"{displayName.ljust(50)} ⏭️ {EMPTY_PROGRESS_BAR} No content to mirror for MAS release {release}")
                continue

            if self._isUnsupportedPackage(version, packageName):
                continue

            # Remove any +buildnum properties from the version in the metadata file
            try:
                version = version.split("+")[0]
            except AttributeError:
                # This likely means we have the perReleaseVersions configuration incorrect
                logger.exception(f"Failed to parse version for {packageName} ({catalogKey}) from catalog: {catalogVersion}")
                raise

            # Get the flag value from args, or use mirrorAll if --all is set
            flag = mirrorAll or getattr(args, argName.replace("-", "_"))

            packageResult = mirrorPackage(
                package=packageName,
                version=version,
                arch=arch,
                mode=mode,
                targetRegistry=targetRegistry,
                flag=flag,
                authFilePath=authFilePath,
                rootDir=rootDir,
                destTlsVerify=destTlsVerify,
                imageTimeout=imageTimeout
            )

            # Track package results (only count if flag was enabled)
            if flag:
                totalImages += packageResult.images
                mirroredImages += packageResult.mirrored
                if not packageResult.success:
                    failedMirrors.append(packageResult)

        # Report final status
        if len(failedMirrors) > 0:
            failedImages = totalImages - mirroredImages
            print_formatted_text(HTML("\n<B>⚠️  Mirror operation completed with failures</B>\n"))
            print_formatted_text(HTML(f"<ansired>Failed to mirror {failedImages} of {totalImages} images</ansired>"))

            for result in failedMirrors:
                print_formatted_text(HTML(f"<ansired>- {result.name} - {result.failed_count} of {result.images} images failed</ansired>"))
                if result.failed_images:
                    for failed_image in result.failed_images:
                        print_formatted_text(HTML(f"<ansired>  - {failed_image}</ansired>"))
        else:
            print_formatted_text(HTML("\n<B>✅ Mirror operation completed successfully</B>"))
            if totalImages > 0:
                print_formatted_text(HTML(f"Successfully mirrored {mirroredImages} images"))

    def _isUnsupportedPackage(self, version: str, packageName: str) -> bool:
        unsupported = False
        if packageName == "ibm-aiservice-tenant" and version.startswith("9.1."):
            logger.warning("Skipping mirroring package 'ibm-aiservice-tenant' due to unsupported version, only supported for 9.2.x or higher")
            unsupported = True
        return unsupported
