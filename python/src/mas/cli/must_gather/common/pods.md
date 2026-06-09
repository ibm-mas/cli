# Pod Collection Architecture

This document explains the pod collection flow in the must-gather tool, detailing how pod discovery, task generation, and parallel collection work together.

## Overview

Pod collection uses a two-phase approach: **discovery** (during planning) and **parallel collection** (during execution). This architecture enables efficient collection of pod metadata, YAML definitions, and container logs across multiple namespaces.

## Collection Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Discovery (Planning Phase)                         │
│ - generatePodCollectionTasks() discovers all pods           │
│ - Uses CoreV1Api.list_namespaced_pod() (thread-safe)        │
│ - Generates pods.md summary with links                      │
│ - Creates one task per pod for parallel execution           │
│ - Returns task list: [(name, _processPod, args), ...]       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Parallel Collection (Execution Phase)              │
│ - Each pod task runs in shared 50-worker threadpool         │
│ - _processPod() writes YAML and collects logs               │
│ - Pods organized by app label into subdirectories           │
│ - Container logs collected sequentially per pod             │
└─────────────────────────────────────────────────────────────┘
```

## Key Functions

### generatePodCollectionTasks()

**Purpose**: Discover all pods in a namespace and generate collection tasks

**When Called**: During planning phase (main thread)

**What It Does**:
1. Creates directory structure: `resources/{namespace}/pods/`
2. Uses `CoreV1Api.list_namespaced_pod()` to discover all pods (thread-safe, no DynamicClient cache)
3. Generates `pods.md` summary with pod status and log links
4. Creates one task tuple per pod: `(task_name, _processPod, dynClient, namespace, pod, podsDir, podLogs)`
5. Returns task list for execution by shared threadpool

**Thread Safety**: Uses `CoreV1Api` directly instead of `DynamicClient.resources.get()` to avoid cache race conditions

**Parameters**:
- `dynClient`: Kubernetes Dynamic Client (for API client configuration)
- `namespace`: Target namespace
- `outputDir`: Base output directory
- `podLogs`: Whether to collect container logs

**Returns**: List of task tuples, one per pod

### _processPod()

**Purpose**: Process a single pod (write YAML and collect logs)

**When Called**: During execution phase (worker thread)

**What It Does**:
1. Extracts pod metadata and converts to dictionary
2. Determines app label for organization (job-name → app → derived from name)
3. Creates app-specific subdirectory: `pods/{appLabel}/`
4. Writes pod YAML: `pods/{appLabel}/{podName}.yaml`
5. If `podLogs=True`, calls `_collectLogs()` to collect container logs

**Thread Safety**: Each pod task runs independently in worker thread. Uses `CoreV1Api(dynClient.client)` for log collection (thread-safe).

**Parameters**:
- `dynClient`: Kubernetes Dynamic Client
- `namespace`: Pod namespace
- `pod`: Pod object from CoreV1Api
- `podsDir`: Base pods directory
- `podLogs`: Whether to collect logs

**Returns**: `True` if successful, `False` on error

### _collectLogs()

**Purpose**: Collect logs for all containers in a pod

**When Called**: From `_processPod()` if `podLogs=True`

**What It Does**:
1. Creates logs subdirectory: `pods/{appLabel}/logs/`
2. Iterates through all container statuses
3. Calls `_collectContainerLogs()` for each container (sequential, no nested parallelism)

**Why Sequential**: Pods are already processed in parallel by the main threadpool. Sequential container processing within each pod avoids nested parallelism and simplifies error handling.

**Parameters**:
- `dynClient`: Kubernetes Dynamic Client
- `namespace`: Pod namespace
- `podName`: Pod name
- `podDict`: Pod dictionary
- `appDir`: App directory for log storage

### _collectContainerLogs()

**Purpose**: Collect current and previous logs for a single container

**When Called**: From `_collectLogs()` for each container

**What It Does**:
1. Creates `CoreV1Api` instance using `dynClient.client`
2. Collects current logs: `{podName}_{containerName}.log`
3. Attempts to collect previous logs: `{podName}_{containerName}_prev.log`
4. Gracefully handles missing previous logs (normal for new containers)

**Thread Safety**: Creates new `CoreV1Api` instance per call using shared API client configuration

**Parameters**:
- `dynClient`: Kubernetes Dynamic Client
- `namespace`: Pod namespace
- `podName`: Pod name
- `containerName`: Container name
- `logsDir`: Directory for log storage

## Pod Organization

Pods are organized by app label into subdirectories for better navigation:

```
resources/
└── {namespace}/
    ├── pods.md                          # Summary with links
    └── pods/
        ├── {app1}/
        │   ├── {pod1}.yaml
        │   ├── {pod2}.yaml
        │   └── logs/
        │       ├── {pod1}_{container1}.log
        │       ├── {pod1}_{container1}_prev.log
        │       ├── {pod2}_{container1}.log
        │       └── {pod2}_{container2}.log
        └── {app2}/
            ├── {pod3}.yaml
            └── logs/
                └── {pod3}_{container1}.log
```

### App Label Extraction

The `_extractAppLabel()` function determines pod organization using this priority:

1. **job-name label**: For job pods (e.g., `mas-inst1-core-upgrade-job`)
2. **app label**: Standard Kubernetes app label
3. **Derived from pod name**: Removes hash suffixes (e.g., `mas-inst1-core-api-7d8f9c-x5k2p` → `mas-inst1-core-api`)

## Thread Safety Considerations

### Why CoreV1Api Instead of DynamicClient?

The `DynamicClient.resources.get()` method uses an internal `_cache` dictionary that is **not thread-safe**. When 50 worker threads simultaneously call `resources.get(kind="Pod")`, they race to populate the cache, causing `KeyError` exceptions.

**Solution**: Use `CoreV1Api.list_namespaced_pod()` directly, which:
- Bypasses the DynamicClient resource cache
- Is thread-safe when using shared API client configuration
- Provides the same pod data in a compatible format

### API Client Sharing

All functions use `CoreV1Api(dynClient.client)` to create API instances with shared configuration:
- `dynClient.client` provides the base API client configuration
- Each `CoreV1Api` instance is independent but shares the underlying HTTP client
- This approach is thread-safe and efficient

## Summary Generation

The `_writeSummary()` function creates a markdown table with:
- Pod name (linked to YAML file)
- Ready status (e.g., "2/2")
- Phase (Running, Pending, Failed, etc.)
- Restart count
- Container log links (if `podLogs=True`)

Example:

```markdown
# Pods (v1)

| NAME | READY | STATUS | RESTARTS | LOGS |
| --- | --- | --- | --- | --- |
| [pod1](pods/app1/pod1.yaml) | 2/2 | Running | 0 | [container1](pods/app1/logs/pod1_container1.log)<br>[container2](pods/app1/logs/pod1_container2.log) |
| [pod2](pods/app1/pod2.yaml) | 1/1 | Running | 3 | [container1](pods/app1/logs/pod2_container1.log) |
```

## Performance Characteristics

- **Discovery**: Fast (~1-2 seconds per namespace) - single API call per namespace
- **Collection**: Parallel execution across all pods in shared 50-worker threadpool
- **Logs**: Sequential per pod (avoids nested parallelism), but pods processed in parallel
- **Scalability**: Handles hundreds of pods efficiently through parallel processing

## Error Handling

- **Discovery errors**: Logged as warnings, returns empty task list
- **Pod processing errors**: Logged as warnings, continues with other pods
- **Log collection errors**: Logged as debug (current) or silently ignored (previous)
- **Missing previous logs**: Normal condition, not logged as error