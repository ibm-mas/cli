#!/bin/bash
set -e

echo "Installing redis-cli..."

# Detect the package manager and install redis-cli accordingly
if command -v microdnf &> /dev/null; then
    # UBI minimal images use microdnf
    echo "Detected microdnf (UBI minimal)"
    # Enable EPEL for redis package
    microdnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm || true
    # Enable redis module stream for RHEL 9
    microdnf module enable -y redis:7 2>/dev/null || true
    microdnf install -y redis && microdnf clean all
elif command -v dnf &> /dev/null; then
    # RHEL 8+/Fedora use dnf
    echo "Detected dnf (RHEL/Fedora)"
    # Try to enable EPEL repository for RHEL/UBI
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm 2>/dev/null || \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm 2>/dev/null || \
    echo "EPEL already installed or not needed"
    
    # Enable redis module stream for RHEL 9 (required for modular filtering)
    dnf module enable -y redis:7 2>/dev/null || \
    dnf module enable -y redis 2>/dev/null || \
    echo "Redis module not available or already enabled"
    
    # Install redis
    dnf install -y redis && dnf clean all
elif command -v yum &> /dev/null; then
    # RHEL 7 and older use yum
    echo "Detected yum (RHEL 7)"
    yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm || true
    yum install -y redis && yum clean all
elif command -v apt-get &> /dev/null; then
    # Debian/Ubuntu use apt-get
    echo "Detected apt-get (Debian/Ubuntu)"
    apt-get update && apt-get install -y redis-tools && rm -rf /var/lib/apt/lists/*
elif command -v apk &> /dev/null; then
    # Alpine uses apk
    echo "Detected apk (Alpine)"
    apk add --no-cache redis
else
    echo "ERROR: No supported package manager found (microdnf, dnf, yum, apt-get, or apk)"
    exit 1
fi

# Verify installation
if command -v redis-cli &> /dev/null; then
    echo "redis-cli installed successfully"
    redis-cli --version
else
    echo "ERROR: redis-cli installation failed"
    exit 1
fi

# Made with Bob
