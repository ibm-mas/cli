# Redis-Based GitOps Locking for IBM Toolchain

## Overview

This guide explains how to configure and use Redis-based distributed locking in IBM Toolchain to avoid Git branch locking issues when multiple pipelines run concurrently.

## Important Behavior Change

Redis locking is now the **preferred** mechanism for migrated GitOps flows that use `gitops_lock_and_modify`.

**Automatic Fallback**: If Redis is unavailable or misconfigured, the system automatically falls back to Git branch-based locking to ensure operations continue.

This provides resilience while maintaining the performance benefits of Redis when available.

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

### Runtime Requirements

For optimal performance with migrated GitOps flows:
- Set `GITOPS_USE_REDIS_LOCKING=true` to enable Redis locking (recommended)
- Ensure Redis is reachable from the pipeline runtime
- Configure valid Redis auth/TLS settings

**Behavior with `GITOPS_USE_REDIS_LOCKING=true`**: Redis must be available and properly configured. If Redis is unavailable or misconfigured, the operation will fail with an error. This ensures explicit control over the locking mechanism.

**Default behavior**: `GITOPS_USE_REDIS_LOCKING=false` uses Git branch locking (skips Redis entirely). This is the default to avoid breaking changes for existing deployments.

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

### Step 2: Configure Environment Variables for Function Execution

These environment variables must be set in the runtime environment whenever you execute migrated GitOps functions that use `gitops_lock_and_modify`.

Using IBM Toolchain to call these functions is optional. If you are using IBM Toolchain, add them as pipeline environment properties. If you are running the functions from another environment, export the same variables there before execution.

#### Required Environment Variables

| Variable Name | Example Value | Description |
|--------------|---------------|-------------|
| `REDIS_USERNAME` | `ibm_cloud_user` | Redis username from credentials |
| `REDIS_HOST` | `c-abc123.databases.appdomain.cloud` | Redis hostname |
| `REDIS_PORT` | `31234` | Redis port |
| `REDIS_PASSWORD` | `your-redis-password` | Redis password |
| `REDIS_TLS_CA_CERT_B64` | `LS0tLS1CRUdJTi...` | Base64-encoded TLS certificate |
| `GITOPS_USE_REDIS_LOCKING` | `true` | Enable Redis locking with automatic Git fallback (recommended, not default) |
| `REDIS_TLS` | `true` | Enable TLS (required for IBM Cloud) |
| `REDIS_DB` | `0` | Redis database number |

#### If Using IBM Toolchain

Add the variables above in **IBM Toolchain → Pipeline → Environment Properties**.

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
│     ├─ Check GITOPS_USE_REDIS_LOCKING=true                  │
│     ├─ Check Redis availability                             │
│     ├─ If Redis available: Use Redis locking ✓              │
│     └─ If Redis unavailable: Fallback to Git locking ⚠      │
│                                                             │
│  3a. Redis Locking Flow (Preferred):                        │
│     ├─ Acquire Redis lock (atomic SET NX operation)         │
│     ├─ Clone Git repository                                 │
│     ├─ Apply changes (callback function)                    │
│     ├─ Commit and push directly to target branch            │
│     └─ Release Redis lock                                   │
│                                                             │
│  3b. Git Locking Flow (Fallback):                           │
│     ├─ Clone Git repository                                 │
│     ├─ Create and push lock branch                          │
│     ├─ Apply changes (callback function)                    │
│     ├─ Commit to lock branch                                │
│     ├─ Merge lock branch to target branch                   │
│     └─ Delete lock branch                                   │
│                                                             │
│  4. Lock automatically expires after TTL (Redis only)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Atomic Operations**: Redis `SET NX` ensures only one pipeline acquires the lock
2. **No Git Pollution**: No temporary branches are created (when using Redis)
3. **Auto-Expiry**: Locks automatically expire (Redis only)
4. **Faster**: Redis operations are much faster than Git
5. **Resilient**: Automatic fallback to Git locking when `GITOPS_USE_REDIS_LOCKING=true`
6. **Cross-Pipeline**: Works across different Tekton pipelines and jobs
7. **Flexible**: Can use Git-only mode with `GITOPS_USE_REDIS_LOCKING=false`

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

### After: Redis with Git Fallback

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

  # Automatically uses Redis if available, falls back to Git locking if not
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

| Aspect | Old (Git Locking) | New (Redis with Fallback) |
|--------|--------------------|---------------------------|
| Primary lock mechanism | Git branch | Redis key (when available) |
| Lock acquisition | Create/push branch | Atomic `SET NX` (Redis) or branch (Git fallback) |
| Lock release | Delete branch/merge | Delete Redis key or branch |
| Cleanup | Manual branch deletion | TTL-based expiry (Redis) or branch deletion (Git) |
| Speed | Slow | Fast (Redis) or Slow (Git fallback) |
| Failure mode | Git lock branch behavior | Fails if Redis unavailable when `GITOPS_USE_REDIS_LOCKING=true` |
| Control | N/A | `GITOPS_USE_REDIS_LOCKING` (true=Redis-only, false=Git-only, default: false) |
| Resilience | Single mechanism | Single mechanism (explicit control) |

---

## Testing and Verification

### 1. Test Redis Connection

```bash
#!/bin/bash

source /path/to/mascli/functions/gitops_utils

echo "Testing Redis connection..."
if redis_available; then
  echo "✓ Redis is accessible and ready"
  echo "✓ GitOps flows will use Redis locking (optimal performance)"
else
  echo "⚠ Redis is not accessible"
  echo "⚠ GitOps flows will fall back to Git-based locking"
  echo "  (Operations will continue but with reduced performance)"
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
⚠ Redis not available, falling back to Git-based locking
```

**Root Cause**:
- `redis-cli` is not installed in the container image

**Impact**:
- Operations will use Git-based locking (slower but functional)

**Solution** (for optimal performance):
1. Verify CLI image version 19.6.1+
2. Update the image if needed
3. Add `redis-cli` to custom images

### Issue: `⚠ Redis not available, falling back to Git-based locking`

**Symptoms**:
- Pipeline logs show fallback to Git locking
- Operations complete successfully but slower

**Possible Causes**:
1. Wrong host or port
2. Wrong username or password
3. TLS certificate issue
4. Network/firewall issue
5. Redis service unavailable

**Impact**:
- Operations continue using Git-based locking
- Performance is reduced (25-75 seconds overhead vs 0.2-0.7 seconds)

**Manual Test**:
```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT \
  --user $REDIS_USERNAME -a $REDIS_PASSWORD \
  --tls --cacert /tmp/redis-certs/ca-cert.pem \
  PING
```

**Solution**:
- Fix Redis configuration to restore optimal performance
- Or accept Git-based locking performance

### Issue: Want to use Git-only locking

**Scenario**:
- You want to skip Redis entirely and always use Git branch locking

**Solution**:
- Set `GITOPS_USE_REDIS_LOCKING=false`
- This bypasses Redis checks and uses Git branch locking directly

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

### Redis-Based Locking (Current with GITOPS_USE_REDIS_LOCKING=true)
- Lock acquisition: 0.1-0.5 seconds
- Lock release: 0.1-0.2 seconds
- Total overhead: 0.2-0.7 seconds
- Failure mode: Automatic fallback to Git locking if Redis unavailable

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
When `GITOPS_USE_REDIS_LOCKING=true` (recommended), Redis must be available and properly configured.

**With `GITOPS_USE_REDIS_LOCKING=true` (recommended)**:
- Uses Redis for optimal performance
- Requires Redis to be available and properly configured
- Operations will fail if Redis is unavailable
- Provides explicit control over locking mechanism

**With `GITOPS_USE_REDIS_LOCKING=false` (default)**:
- Uses Git-based locking directly
- Skips Redis entirely
- This is the default to avoid breaking changes

---

---

## Summary

✅ `redis-cli` is recommended in the container for optimal performance
✅ Redis environment variables should be configured for best results
✅ `GITOPS_USE_REDIS_LOCKING=true` enables Redis locking (recommended, requires Redis to be available)
✅ All identified Git branch locking functions are migrated
✅ **Explicit control**: Operations fail if Redis is unavailable when `GITOPS_USE_REDIS_LOCKING=true`
✅ Redis locking eliminates Git branch locking issues and branch pollution when available
✅ Git-based locking remains available via `GITOPS_USE_REDIS_LOCKING=false` (default)

**Redis is the preferred locking backend** for migrated GitOps flows, with automatic fallback to Git-based locking for resilience.

### Configuration Modes

| Mode | `GITOPS_USE_REDIS_LOCKING` | Redis Available | Behavior |
|------|---------------------------|----------------|----------|
| **Optimal** | `true` | ✅ Yes | Uses Redis (fast) |
| **Resilient Fallback** | `true` | ❌ No | Falls back to Git (slower but works) |
| **Git-only** | `false` | N/A | Always uses Git (skips Redis) |