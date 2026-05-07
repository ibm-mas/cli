#!/bin/bash
#
# IBM Toolchain Redis Setup Script
# This script extracts Redis credentials from IBM Cloud and generates
# environment variable configuration for IBM Toolchain.
#
# Redis is the preferred locking mechanism for migrated GitOps flows.
# When GITOPS_USE_REDIS_LOCKING=true (recommended):
#   - Uses Redis for optimal performance
#   - Requires Redis to be available (fails if not)
# When GITOPS_USE_REDIS_LOCKING=false (default):
#   - Uses Git branch locking directly
#
# Prerequisites:
#   - IBM Cloud CLI installed: curl -fsSL https://clis.cloud.ibm.com/install/osx | sh
#   - jq installed: brew install jq
#   - redis-cli installed: brew install redis (for local validation only)
#
# Note: redis-cli is automatically included in CLI container image v19.6.1+
#       This script only needs redis-cli locally for connection testing.
#
# Usage:
#   ./docs/ibm-toolchain-redis-setup.sh [redis-instance-name]
#
# Example:
#   ./docs/ibm-toolchain-redis-setup.sh mas-gitops-redis-dev
#

set -e

echo "=========================================="
echo "IBM Cloud Redis Configuration Extractor"
echo "=========================================="
echo ""
echo "Redis is the preferred locking mechanism for migrated GitOps flows."
echo ""
echo "Behavior with GITOPS_USE_REDIS_LOCKING=true (recommended, not default):"
echo "  • Uses Redis for optimal performance"
echo "  • Requires Redis to be available (fails if not)"
echo ""
echo "Default behavior (GITOPS_USE_REDIS_LOCKING=false):"
echo "  • Uses Git branch locking directly"
echo ""

# Check prerequisites
command -v ibmcloud >/dev/null 2>&1 || { echo "Error: IBM Cloud CLI not installed. Run: curl -fsSL https://clis.cloud.ibm.com/install/osx | sh"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq not installed. Run: brew install jq"; exit 1; }
command -v redis-cli >/dev/null 2>&1 || { echo "Error: redis-cli not installed. Run: brew install redis"; exit 1; }

# Get Redis instance name
REDIS_INSTANCE_NAME="${1}"
if [ -z "$REDIS_INSTANCE_NAME" ]; then
    echo "Available Redis instances:"
    ibmcloud resource service-instances --service-name databases-for-redis 2>/dev/null || true
    echo ""
    read -p "Enter Redis instance name: " REDIS_INSTANCE_NAME
fi

if [ -z "$REDIS_INSTANCE_NAME" ]; then
    echo "Error: Redis instance name is required"
    exit 1
fi

echo ""
echo "Using Redis instance: $REDIS_INSTANCE_NAME"
echo ""

# Check if logged in
if ! ibmcloud target >/dev/null 2>&1; then
    echo "Not logged in to IBM Cloud. Logging in..."
    ibmcloud login --sso
fi

# Display current target
echo "Current IBM Cloud target:"
ibmcloud target
echo ""

# Check if service key exists
SERVICE_KEY_NAME="${REDIS_INSTANCE_NAME}-credentials"
echo "Checking for existing service key: $SERVICE_KEY_NAME"

if ibmcloud resource service-key "$SERVICE_KEY_NAME" >/dev/null 2>&1; then
    echo "✓ Service key exists"
else
    echo "Service key not found. Creating new service key..."
    ibmcloud resource service-key-create "$SERVICE_KEY_NAME" \
        --instance-name "$REDIS_INSTANCE_NAME"

    if [ $? -eq 0 ]; then
        echo "✓ Service key created successfully"
    else
        echo "✗ Failed to create service key"
        exit 1
    fi
fi

echo ""
echo "Extracting credentials..."

# Create temporary file for credentials
TEMP_CREDS_FILE="/tmp/redis-credentials-$$.json"
ibmcloud resource service-key "$SERVICE_KEY_NAME" --output json > "$TEMP_CREDS_FILE"

# Extract connection details
REDIS_HOST=$(jq -r '.[0].credentials.connection.rediss.hosts[0].hostname' "$TEMP_CREDS_FILE")
REDIS_PORT=$(jq -r '.[0].credentials.connection.rediss.hosts[0].port' "$TEMP_CREDS_FILE")
REDIS_PASSWORD=$(jq -r '.[0].credentials.connection.rediss.authentication.password' "$TEMP_CREDS_FILE")
REDIS_USERNAME=$(jq -r '.[0].credentials.connection.rediss.authentication.username' "$TEMP_CREDS_FILE")

# Extract and encode certificate
TEMP_CERT_FILE="/tmp/redis-cert-$$.crt"
jq -r '.[0].credentials.connection.rediss.certificate.certificate_base64' "$TEMP_CREDS_FILE" | base64 -d > "$TEMP_CERT_FILE"

# Get base64 encoded certificate for environment variable
REDIS_TLS_CA_CERT_B64=$(jq -r '.[0].credentials.connection.rediss.certificate.certificate_base64' "$TEMP_CREDS_FILE")

# Set defaults
REDIS_TLS="true"
REDIS_DB="0"

# Display extracted credentials (password masked)
echo ""
echo "Extracted Redis Credentials:"  # pragma: allowlist secret
echo "  Username: $REDIS_USERNAME"
echo "  Password: ${REDIS_PASSWORD:0:8}****"
echo "  Host: $REDIS_HOST"
echo "  Port: $REDIS_PORT"
echo "  TLS: $REDIS_TLS"
echo "  Database: $REDIS_DB"
echo ""

# Optional tuning parameters
echo "Lock Behavior Tuning (using defaults, can be changed in IBM Toolchain):"
GITOPS_LOCK_TTL="300"
GITOPS_LOCK_RETRY_MAX="100"
GITOPS_LOCK_RETRY_DELAY="20"
echo "  Lock TTL: ${GITOPS_LOCK_TTL}s"
echo "  Max Retries: $GITOPS_LOCK_RETRY_MAX"
echo "  Retry Delay: ${GITOPS_LOCK_RETRY_DELAY}s"

# Test connection
echo ""
echo "=========================================="
echo "Testing Redis Connection..."
echo "=========================================="

# Test PING
echo "Testing: redis-cli PING"
if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
    --user "$REDIS_USERNAME" \
    -a "$REDIS_PASSWORD" \
    --tls --cacert "$TEMP_CERT_FILE" \
    PING > /dev/null 2>&1; then
    echo "✓ PING successful"
else
    echo "✗ PING failed"
    echo "⚠ Redis is not reachable - GitOps flows will fall back to Git-based locking"
    echo "  (Operations will continue but with reduced performance)"
    rm -f "$TEMP_CERT_FILE" "$TEMP_CREDS_FILE"
    exit 1
fi

# Test SET/GET
echo "Testing: SET/GET operations"
TEST_KEY="ibm-toolchain-test-$$"
TEST_VALUE="Hello from IBM Toolchain"

if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
    --user "$REDIS_USERNAME" \
    -a "$REDIS_PASSWORD" \
    --tls --cacert "$TEMP_CERT_FILE" \
    SET "$TEST_KEY" "$TEST_VALUE" EX 60 > /dev/null 2>&1; then
    echo "✓ SET successful"
else
    echo "✗ SET failed"
    rm -f "$TEMP_CERT_FILE" "$TEMP_CREDS_FILE"
    exit 1
fi

RETRIEVED_VALUE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
    --user "$REDIS_USERNAME" \
    -a "$REDIS_PASSWORD" \
    --tls --cacert "$TEMP_CERT_FILE" \
    GET "$TEST_KEY" 2>/dev/null)

if [ "$RETRIEVED_VALUE" == "$TEST_VALUE" ]; then
    echo "✓ GET successful"
    echo "✓ All Redis operations working correctly!"
else
    echo "✗ GET failed or value mismatch"
    rm -f "$TEMP_CERT_FILE" "$TEMP_CREDS_FILE"
    exit 1
fi

# Cleanup test key
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
    --user "$REDIS_USERNAME" \
    -a "$REDIS_PASSWORD" \
    --tls --cacert "$TEMP_CERT_FILE" \
    DEL "$TEST_KEY" > /dev/null 2>&1

# Cleanup temporary files
rm -f "$TEMP_CERT_FILE" "$TEMP_CREDS_FILE"

# Generate output
echo ""
echo "=========================================="
echo "IBM Toolchain Environment Variables"
echo "=========================================="
echo ""
echo "Copy these to: IBM Toolchain → Pipeline → Environment Properties"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "REQUIRED VARIABLES (mark sensitive values as 'Secure' type)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "REDIS_USERNAME (Secure): $REDIS_USERNAME"
echo "REDIS_HOST (Text): $REDIS_HOST"
echo "REDIS_PORT (Text): $REDIS_PORT"
echo "REDIS_PASSWORD (Secure): ${REDIS_PASSWORD:0:8}****"  # pragma: allowlist secret
echo "REDIS_TLS_CA_CERT_B64 (Secure): ${REDIS_TLS_CA_CERT_B64:0:50}..."
echo "REDIS_TLS (Text): $REDIS_TLS"
echo "REDIS_DB (Text): $REDIS_DB"
echo "GITOPS_USE_REDIS_LOCKING (Text): true"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPTIONAL TUNING VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "GITOPS_LOCK_TTL (Text): $GITOPS_LOCK_TTL (Lock expires after N seconds)"
echo "GITOPS_LOCK_RETRY_MAX (Text): $GITOPS_LOCK_RETRY_MAX (Max retry attempts)"
echo "GITOPS_LOCK_RETRY_DELAY (Text): $GITOPS_LOCK_RETRY_DELAY (Seconds between retries)"
echo ""

# Save configuration files
OUTPUT_FILE="redis-toolchain-config-$(date +%Y%m%d-%H%M%S).txt"
cat > "$OUTPUT_FILE" << EOF
IBM Toolchain Redis Configuration
Generated: $(date)
Instance: $REDIS_INSTANCE_NAME

IMPORTANT:
When GITOPS_USE_REDIS_LOCKING=true (recommended, not default):
  - Uses Redis for optimal performance
  - Requires Redis to be available (fails if not)
When GITOPS_USE_REDIS_LOCKING=false (default):
  - Uses Git branch locking directly

REQUIRED VARIABLES:
REDIS_USERNAME=$REDIS_USERNAME
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_TLS_CA_CERT_B64=$REDIS_TLS_CA_CERT_B64
REDIS_TLS=$REDIS_TLS
REDIS_DB=$REDIS_DB
GITOPS_USE_REDIS_LOCKING=true

OPTIONAL TUNING:
GITOPS_LOCK_TTL=$GITOPS_LOCK_TTL
GITOPS_LOCK_RETRY_MAX=$GITOPS_LOCK_RETRY_MAX
GITOPS_LOCK_RETRY_DELAY=$GITOPS_LOCK_RETRY_DELAY
EOF

JSON_FILE="redis-toolchain-config-$(date +%Y%m%d-%H%M%S).json"
cat > "$JSON_FILE" << EOF
{
  "redis_instance": "$REDIS_INSTANCE_NAME",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "notes": [
    "GITOPS_USE_REDIS_LOCKING=true: Uses Redis, requires it to be available (recommended, not default)",
    "GITOPS_USE_REDIS_LOCKING=false: Uses Git branch locking directly (default)"
  ],
  "environment_variables": {
    "REDIS_USERNAME": "$REDIS_USERNAME",
    "REDIS_HOST": "$REDIS_HOST",
    "REDIS_PORT": "$REDIS_PORT",
    "REDIS_PASSWORD": "$REDIS_PASSWORD",
    "REDIS_TLS_CA_CERT_B64": "$REDIS_TLS_CA_CERT_B64",
    "REDIS_TLS": "$REDIS_TLS",
    "REDIS_DB": "$REDIS_DB",
    "GITOPS_USE_REDIS_LOCKING": "true",
    "GITOPS_LOCK_TTL": "$GITOPS_LOCK_TTL",
    "GITOPS_LOCK_RETRY_MAX": "$GITOPS_LOCK_RETRY_MAX",
    "GITOPS_LOCK_RETRY_DELAY": "$GITOPS_LOCK_RETRY_DELAY"
  }
}
EOF

echo "Configuration saved to: $OUTPUT_FILE"
echo "JSON configuration saved to: $JSON_FILE"
echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Add Environment Variables to IBM Toolchain:"
echo "   • Go to: IBM Toolchain → Your Pipeline → Environment Properties"
echo "   • Add each variable listed above"
echo "   • Mark REDIS_USERNAME, REDIS_PASSWORD, and REDIS_TLS_CA_CERT_B64 as 'Secure'"
echo ""
echo "2. Verify Configuration:"
echo "   • Review: $OUTPUT_FILE"
echo "   • JSON format: $JSON_FILE"
echo "   • Keep these files secure (contain sensitive credentials)"
echo ""
echo "3. Verify Container Image:"
echo "   • Ensure CLI image version is 19.6.1+ (includes redis-cli)"
echo "   • Or add redis-cli to custom images (see docs/redis-locking-setup.md)"
echo ""
echo "4. Deploy and Test:"
echo "   • Deploy your updated pipeline"
echo "   • Monitor logs for 'Using Redis-based distributed locking' (optimal)"
echo "   • If you see '⚠ Redis not available, falling back to Git-based locking', operations will continue but slower"
echo "   • If you see 'redis-cli command not found', update your CLI image for optimal performance"
echo ""
echo "5. Optional: Use Git-Only Locking:"
echo "   • Set GITOPS_USE_REDIS_LOCKING=false to always use Git branch locking"
echo "   • Default is true (Redis preferred with automatic fallback)"
echo ""
echo "6. Documentation:"
echo "   • See: docs/redis-locking-setup.md"
echo "   • See: docs/MIGRATION_COMPLETE_SUMMARY.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  SECURITY REMINDER:"
echo "   • Store $OUTPUT_FILE and $JSON_FILE securely"
echo "   • Do not commit these files to Git"
echo "   • Use IBM Toolchain's 'Secure' property type for sensitive values"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
