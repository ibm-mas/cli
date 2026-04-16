# Redis-Based GitOps Locking for IBM Toolchain

## Overview

This guide explains how to configure and use Redis-based distributed locking in IBM Toolchain to avoid Git branch locking issues when multiple pipelines run concurrently.

## Important Behavior Change

Redis locking is now required for migrated GitOps flows that use `gitops_lock_and_modify`.

There is no longer any fallback to Git branch locking.

If Redis is unavailable, misconfigured, or disabled, migrated GitOps operations fail immediately.

---

## Problem Statement

The previous Git branch-based locking (`clone_and_lock_target_git_repo`) had these limitations:
- **Race conditions**: Multiple pipelines can create duplicate commits
- **Merge conflicts**: Concurrent updates cause unresolvable conflicts
- **Branch pollution**: Temporary lock branches clutter the repository
- **Slow operations**: Git operations are slower than Redis
- **Orphaned locks**: Failed pipelines can leave lock branches behind

## Solution: Redis Distributed Locking

Redis provides atomic operations for distributed locking that eliminate these issues.

---

## Prerequisites

### Container Image Requirements

The CLI container image **must have `redis-cli` installed** to use Redis-based locking.

**Status**: ✅ As of version 19.6.1+, `redis-cli` is automatically installed in the CLI container image.

If you're using an older version or custom image, ensure `redis-cli` is available:

```bash
redis-cli --version
```

If not installed, see the [Container Image Setup](#container-image-setup) section below.

### Required Runtime Requirement

For migrated GitOps flows:
- `GITOPS_USE_REDIS_LOCKING` must be `true`
- Redis must be reachable from the pipeline runtime
- Redis auth/TLS settings must be valid

If any of these are not true, the operation fails.

---

## IBM Cloud Redis Setup

### Step 1: Get Redis Credentials from IBM Cloud

1. Navigate to your IBM Cloud Redis instance
2. Go to **Service Credentials** → **View Credentials**
3. Extract the following values:

```json
{
  "connection": {
    "rediss": {
      "hosts": [
        {
          "hostname": "c-abc123.databases.appdomain.cloud",
          "port": 31234
        }
      ],
      "authentication": {
        "username": "ibm_cloud_user",
        "password": "your-redis-password"  # pragma: allowlist secret
      },
      "certificate": {
        "certificate_base64": "LS0tLS1CRUdJTi..."
      }
    }
  }
}
```

### Step 2: Configure IBM Toolchain Environment Variables

Add these environment variables to your IBM Toolchain pipeline.

#### In IBM Toolchain → Pipeline → Environment Properties:

| Variable Name | Type | Value | Description |
|--------------|------|-------|-------------|
| `REDIS_USERNAME` | Secure | `ibm_cloud_user` | Redis username from credentials |
| `REDIS_HOST` | Text | `c-abc123.databases.appdomain.cloud` | Redis hostname |
| `REDIS_PORT` | Text | `31234` | Redis port |
| `REDIS_PASSWORD` | Secure | `your-redis-password` | Redis password |
| `REDIS_TLS_CA_CERT_B64` | Secure | `LS0tLS1CRUdJTi...` | Base64-encoded TLS certificate |
| `GITOPS_USE_REDIS_LOCKING` | Text | `true` | Required for migrated locking flows |
| `REDIS_TLS` | Text | `true` | Enable TLS (required for IBM Cloud) |
| `REDIS_DB` | Text | `0` | Redis database number |

#### Optional Tuning Parameters

| Variable Name | Default | Description |
|--------------|---------|-------------|
| `GITOPS_LOCK_TTL` | `300` | Lock expires after N seconds |
| `GITOPS_LOCK_RETRY_MAX` | `100` | Maximum retry attempts |
| `GITOPS_LOCK_RETRY_DELAY` | `20` | Seconds between retry attempts |

---

## How It Works

### Architecture Flow

```text
┌─────────────────────────────────────────────────────────────┐
│                    IBM Toolchain Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Pipeline starts → Load Redis credentials from secrets   │
│                                                             │
│  2. Call gitops_lock_and_modify()                           │
│     ├─ Verify GITOPS_USE_REDIS_LOCKING=true                 │
│     ├─ Check Redis availability                             │
│     ├─ If YES: Use Redis locking ✓                          │
│     └─ If NO: Fail immediately                              │
│                                                             │
│  3. Redis Locking Flow:                                     │
│     ├─ Acquire Redis lock (atomic SET NX operation)         │
│     ├─ Clone Git repository                                 │
│     ├─ Apply changes (callback function)                    │
│     ├─ Commit and push directly to target branch            │
│     └─ Release Redis lock                                   │
│                                                             │
│  4. Lock automatically expires after TTL                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Atomic Operations**: Redis `SET NX` ensures only one pipeline acquires the lock
2. **No Git Pollution**: No temporary branches are created
3. **Auto-Expiry**: Locks automatically expire
4. **Faster**: Redis operations are much faster than Git
5. **Explicit Failure Mode**: Misconfigured Redis fails fast instead of silently changing behavior
6. **Cross-Pipeline**: Works across different Tekton pipelines and jobs

---

## Code Migration Guide

### Before: Old Git-Based Locking

```bash
GIT_LOCK_BRANCH=$(git_lock_branch_name "gitops-cp4d-service" "${ACCOUNT_ID}" "${CLUSTER_ID}" "${MAS_INSTANCE_ID}")

if [ "$GITHUB_PUSH" == "true" ]; then
  clone_and_lock_target_git_repo "${GITHUB_HOST}" "${GITHUB_ORG}" "${GITHUB_REPO}" \
    "${GIT_BRANCH}" "${GITOPS_WORKING_DIR}" "${GIT_SSH}" "${GIT_LOCK_BRANCH}"
fi

mkdir -p ${GITOPS_INSTANCE_DIR}
jinjanate_commmon template.j2 ${GITOPS_INSTANCE_DIR}/config.yaml

if [ "$GITHUB_PUSH" == "true" ]; then
  save_and_unlock_target_git_repo "${GITHUB_REPO}" "${GIT_BRANCH}" "${GITOPS_WORKING_DIR}" \
    "${GIT_COMMIT_MSG}" "${GIT_LOCK_BRANCH}" CONFIG_CHANGED
  remove_git_repo_clone $GITOPS_WORKING_DIR/$GITHUB_REPO
fi
```

### After: Redis-Required Locking

```bash
function apply_cp4d_service_changes() {
  local GITOPS_REPO_DIR="$1"
  local GITOPS_INSTANCE_DIR="${GITOPS_REPO_DIR}/${ACCOUNT_ID}/${CLUSTER_ID}/${MAS_INSTANCE_ID}"

  mkdir -p "${GITOPS_INSTANCE_DIR}"
  jinjanate_commmon template.j2 "${GITOPS_INSTANCE_DIR}/config.yaml"
  return 0
}

if [ "$GITHUB_PUSH" == "true" ]; then
  LOCK_NAME="gitops-cp4d-service.${ACCOUNT_ID}.${CLUSTER_ID}.${MAS_INSTANCE_ID}"

  gitops_lock_and_modify \
    "${GITHUB_HOST}" \
    "${GITHUB_ORG}" \
    "${GITHUB_REPO}" \
    "${GIT_BRANCH}" \
    "${GITOPS_WORKING_DIR}" \
    "${GIT_SSH}" \
    "${LOCK_NAME}" \
    "apply_cp4d_service_changes" \
    "${GIT_COMMIT_MSG}" \
    CONFIG_CHANGED

  if [[ "${CONFIG_CHANGED}" == "1" ]]; then
    echo "Configuration was modified and pushed"
  fi
else
  mkdir -p ${GITOPS_INSTANCE_DIR}
  apply_cp4d_service_changes "${GITOPS_WORKING_DIR}/${GITHUB_REPO}"
fi
```

### Key Differences

| Aspect | Old (Git Locking) | New (Redis Locking) |
|--------|--------------------|---------------------|
| Lock mechanism | Git branch | Redis key |
| Lock acquisition | Create/push branch | Atomic `SET NX` |
| Lock release | Delete branch/merge | Delete Redis key |
| Cleanup | Manual branch deletion | TTL-based expiry |
| Speed | Slow | Fast |
| Failure mode | Git lock branch behavior | Fail fast if Redis unavailable |
| Fallback | N/A | None |

---

## Testing and Verification

### 1. Test Redis Connection

```bash
#!/bin/bash

source /path/to/mascli/functions/gitops_utils

echo "Testing Redis connection..."
if redis_available; then
  echo "✓ Redis is accessible and ready"
  echo "✓ Migrated GitOps flows can run"
else
  echo "✗ Redis is not accessible"
  echo "✗ Migrated GitOps flows will fail"
  exit 1
fi
```

### 2. Monitor Active Locks

```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT \
  --user $REDIS_USERNAME -a $REDIS_PASSWORD \
  --tls --cacert /tmp/redis-certs/ca-cert.pem \
  KEYS "gitops:lock:*"
```

### 3. Check Specific Lock

```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT \
  --user $REDIS_USERNAME -a $REDIS_PASSWORD \
  --tls --cacert /tmp/redis-certs/ca-cert.pem \
  GET "gitops:lock:gitops-config:gitops-cp4d-service.account.cluster.instance"
```

### 4. Emergency Lock Release

```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT \
  --user $REDIS_USERNAME -a $REDIS_PASSWORD \
  --tls --cacert /tmp/redis-certs/ca-cert.pem \
  DEL "gitops:lock:gitops-config:gitops-cp4d-service.account.cluster.instance"
```

---

## Migration Status

### Completed Migrations

The following functions have been migrated:
- `gitops_cp4d_service`
- `gitops_suite_app_config`
- `gitops_deprovision_app_config`
- `gitops_mas_config`
- `gitops_suite_workspace`
- `gitops_deprovision_suite_workspace`
- `gitops_deprovision_cp4d_service`
- `gitops_db2u_database`
- `gitops_rds_db2_database`
- `gitops_deprovision_db2u_database`

Migration completion:
- Migrated: 10
- Remaining: 0

---

## Troubleshooting

### Issue: `redis-cli command not found in PATH`

**Symptoms**:
```text
redis-cli command not found in PATH
ERROR: Redis locking is required but Redis is not available
```

**Root Cause**:
- `redis-cli` is not installed in the container image

**Solution**:
1. Verify CLI image version 19.6.1+
2. Update the image if needed
3. Add `redis-cli` to custom images

### Issue: `ERROR: Redis locking is required but Redis is not available`

**Symptoms**:
- Migrated pipeline fails before lock acquisition

**Possible Causes**:
1. Wrong host or port
2. Wrong username or password
3. TLS certificate issue
4. Network/firewall issue
5. Redis service unavailable

**Manual Test**:
```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT \
  --user $REDIS_USERNAME -a $REDIS_PASSWORD \
  --tls --cacert /tmp/redis-certs/ca-cert.pem \
  PING
```

### Issue: `ERROR: Redis locking is required but GITOPS_USE_REDIS_LOCKING is not set to true`

**Cause**:
- Pipeline configuration is incomplete

**Solution**:
- Set `GITOPS_USE_REDIS_LOCKING=true`

### Issue: `Failed to acquire lock after N attempts`

**Cause**:
- Another process holds the same lock

**Solutions**:
1. Wait for lock release
2. Check active locks
3. Increase retry settings if necessary

---

## Performance Comparison

### Git-Based Locking (Old)
- Lock acquisition: 10-30 seconds
- Lock release: 15-45 seconds
- Total overhead: 25-75 seconds
- Failure mode: Orphaned branches/manual cleanup

### Redis-Based Locking (Current)
- Lock acquisition: 0.1-0.5 seconds
- Lock release: 0.1-0.2 seconds
- Total overhead: 0.2-0.7 seconds
- Failure mode: Explicit fail-fast if Redis unavailable

**Performance Improvement: ~50-100x faster**

---

## Support and Maintenance

### Monitoring
Monitor:
- Redis connection count
- Lock acquisition success rate
- Average lock duration
- Failed lock acquisitions

### Alerts
Set up alerts for:
- Redis unavailable
- High lock contention
- Excessive retries
- Unexpected lock duration

### Operational Note
If Redis becomes unavailable, migrated GitOps flows stop until Redis connectivity is restored.

This is expected behavior.

---

## Container Image Setup

### Adding redis-cli to Custom Images

If you're building a custom CLI image, add redis-cli installation.

**1. Create installation script** (`image/cli/install/install-redis-cli.sh`):
```bash
#!/bin/bash
set -e

echo "Installing redis-cli..."

if command -v microdnf &> /dev/null; then
    microdnf install -y redis && microdnf clean all
elif command -v dnf &> /dev/null; then
    dnf install -y redis && dnf clean all
elif command -v yum &> /dev/null; then
    yum install -y redis && yum clean all
elif command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y redis-tools && rm -rf /var/lib/apt/lists/*
elif command -v apk &> /dev/null; then
    apk add --no-cache redis
else
    echo "ERROR: No supported package manager found"
    exit 1
fi

redis-cli --version
```

**2. Update Dockerfile** (`image/cli/Dockerfile`):
```dockerfile
COPY install /tmp/install
RUN bash /tmp/install/install-redis-cli.sh && \
    bash /tmp/install/install-python-packages.sh
```

---

## Summary

✅ `redis-cli` is required in the container  
✅ Redis environment variables must be configured  
✅ `GITOPS_USE_REDIS_LOCKING=true` is required  
✅ All identified Git branch locking functions are migrated  
✅ No fallback to Git locking remains in `gitops_lock_and_modify`  
✅ Fail-fast behavior is now enforced  
✅ Redis locking eliminates Git branch locking issues and branch pollution  

Redis is now the required locking backend for migrated GitOps flows.