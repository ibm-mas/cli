# MAS Must-Gather Tool

## Overview

The MAS Must-Gather tool collects diagnostic information from IBM Maximo Application Suite (MAS) installations on OpenShift clusters. It gathers cluster resources, application configurations, logs, and other diagnostic data into a compressed archive for troubleshooting and support purposes.

## Architecture

### 4-Phase Collection Process

The must-gather tool uses a parallel collection architecture with four distinct phases:

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: CRD Processing (Upfront)                           │
│ - Process all CustomResourceDefinitions                     │
│ - Extract printer columns for markdown tables               │
│ - Identify IBM CRDs for targeted collection                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Discovery (~5 seconds)                             │
│ - Discover all namespaces to collect                        │
│ - Identify MAS instances and applications                   │
│ - Generate complete CollectionPlan with all tasks           │
│ - NO data collection in this phase                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Parallel Collection (200-300 seconds)              │
│ - Execute all tasks using shared 50-worker threadpool       │
│ - Collect resources, secrets, pods, logs in parallel        │
│ - Sequential UI presentation for user feedback              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Summary & Packaging (~30 seconds)                  │
│ - Generate subscriptions summary                            │
│ - Create web viewer manifest                                │
│ - Package into tar.gz archive                               │
│ - Optional upload to Artifactory                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. CRD Processing
**Location**: [`common/crd_processor.py`](common/crd_processor.py)

Processes CustomResourceDefinitions upfront to:
- Extract printer columns for markdown table generation
- Identify IBM CRDs for targeted collection
- Cache results for use throughout collection

See [CRD Processor Documentation](common/crd_processor.md) for technical details.

#### 2. Collection Planning
**Location**: [`app.py:planCollection()`](app.py)

Discovers all resources and generates a complete collection plan:
- OCP cluster resources (nodes, storage, operators)
- Dependencies (Kafka, MongoDB, Grafana, Cert Manager, SLS, DB2, CP4D)
- MAS Core instances
- MAS Applications (Manage, Monitor, IoT, etc.)
- AI Service instances and tenants
- Argo CD applications

**Output**: [`CollectionPlan`](collection_plan.py) containing organized [`CollectionGroup`](collection_plan.py) objects

#### 3. Parallel Execution
**Location**: [`parallel_executor.py`](parallel_executor.py)

Executes collection plan using a single shared threadpool:
- 50 concurrent workers for maximum parallelism
- Sequential UI presentation by collection group
- Graceful error handling per task
- Progress tracking with completion callbacks

#### 4. Task Generation
**Pattern**: Each module provides task generation functions

Example modules:
- [`common/task_generation.py`](common/task_generation.py) - Standard namespace tasks
- [`dependencies/sls.py`](dependencies/sls.py) - SLS-specific tasks
- [`mas/core.py`](mas/core.py) - MAS Core tasks
- [`mas/apps.py`](mas/apps.py) - MAS Application tasks

**Task Format**: `(task_name, function, *args)` tuples

### Collection Modules

#### OpenShift Platform
- **Cluster Resources** ([`ocp/cluster.py`](ocp/cluster.py)) - Storage, versions, namespaces, RBAC
- **Nodes** ([`ocp/nodes.py`](ocp/nodes.py)) - Node information and status
- **Airgap** ([`ocp/airgap.py`](ocp/airgap.py)) - Mirror configurations for disconnected environments
- **Marketplace** ([`ocp/marketplace.py`](ocp/marketplace.py)) - Catalog sources and operator subscriptions

#### Dependencies
- **Kafka** ([`dependencies/kafka.py`](dependencies/kafka.py)) - Strimzi Kafka clusters
- **MongoDB** ([`dependencies/mongodb.py`](dependencies/mongodb.py)) - MongoDB Community Edition
- **Grafana** ([`dependencies/grafana.py`](dependencies/grafana.py)) - Grafana instances
- **Certificate Manager** ([`dependencies/cert_manager.py`](dependencies/cert_manager.py)) - Cert Manager operator
- **SLS** ([`dependencies/sls.py`](dependencies/sls.py)) - IBM Suite License Service
- **DB2** ([`dependencies/db2.py`](dependencies/db2.py)) - IBM Db2 databases
- **CP4D** ([`dependencies/cp4d.py`](dependencies/cp4d.py)) - IBM Cloud Pak for Data

#### MAS Components
- **Core** ([`mas/core.py`](mas/core.py)) - MAS Suite instances
- **Applications** ([`mas/apps.py`](mas/apps.py)) - MAS application workspaces
- **Pipelines** ([`mas/pipelines.py`](mas/pipelines.py)) - Tekton pipelines for MAS

#### AI Service
- **Instances** ([`aiservice/instance.py`](aiservice/instance.py)) - AI Service instances
- **Tenants** ([`aiservice/tenant.py`](aiservice/tenant.py)) - AI Service tenants
- **Pipelines** ([`aiservice/pipelines.py`](aiservice/pipelines.py)) - AI Service pipelines

#### Argo CD
- **Applications** ([`argo/applications.py`](argo/applications.py)) - Argo CD applications

### Common Utilities

#### Resource Collection
- **Resources** ([`common/resources.py`](common/resources.py)) - Generic resource collection with markdown generation
- **Parallel** ([`common/parallel.py`](common/parallel.py)) - Parallel resource collection with progress tracking
- **Pods** ([`common/pods.py`](common/pods.py)) - Pod collection with logs
- **Secrets** ([`common/secrets.py`](common/secrets.py)) - Secret collection (with optional data)
- **Reconcile Logs** ([`common/reconcile_logs.py`](common/reconcile_logs.py)) - Operator reconcile logs from pods

#### IBM Resources
- **IBM Resources** ([`common/ibm_resources.py`](common/ibm_resources.py)) - Targeted collection of IBM CRDs

### Output Management

#### Output Manager
**Location**: [`output.py`](output.py)

Manages output directory structure and archiving:
- Creates timestamped directories
- Organizes resources by namespace
- Generates tar.gz archives
- Handles cleanup based on `--keep-files` flag

#### Web Viewer
**Location**: [`web_viewer/`](web_viewer/)

Generates interactive web viewer for browsing collected data:
- Manifest generation for file tree
- HTML template for viewing
- Namespace-based organization

## Usage

### Basic Collection
```bash
mas must-gather
```

### Filtered Collection
```bash
# Specific MAS instance
mas must-gather --mas-instance-id inst1

# Specific applications
mas must-gather --mas-app-id manage,monitor

# Skip dependencies
mas must-gather --no-dependencies

# Skip OCP resources
mas must-gather --no-ocp
```

### Advanced Options
```bash
# Summary only (no detailed YAML)
mas must-gather --summary-only

# Skip pod logs
mas must-gather --no-logs

# Include secret data
mas must-gather --secret-data

# Keep temporary files
mas must-gather --keep-files
```

## Development

### Adding New Collection Modules

1. **Create discovery function** to identify namespaces/resources
2. **Create task generation function** to define collection tasks
3. **Add to collection plan** in [`app.py:planCollection()`](app.py)
4. **Write tests** following TDD practices

Example:
```python
def discoverMyResourceNamespaces(dynClient: DynamicClient) -> Set[str]:
    """Discover namespaces containing MyResource CRs."""
    # Implementation

def generateMyResourceCollectionTasks(
    dynClient: DynamicClient,
    namespace: str,
    outputDir: str,
    noDetail: bool
) -> List[Tuple[str, Callable, ...]]:
    """Generate collection tasks for MyResource namespace."""
    return [
        ("resources", collectResources, dynClient, namespace, ...),
        ("secrets", collectSecrets, dynClient, namespace, ...),
        ("pods", collectPods, dynClient, namespace, ...),
    ]
```

### Testing

Run tests:
```bash
pytest python/tests/unit/must_gather -v
```

Validate code quality:
```bash
black python/src/mas/cli/must_gather
flake8 python/src/mas/cli/must_gather
basedpyright python/src/mas/cli/must_gather
```

## Performance

### Baseline (Sequential)
- **Total Time**: ~568 seconds
- **Parallelism**: 10-20 concurrent tasks per group
- **Architecture**: New threadpool per collection group

### Optimized (Parallel)
- **Total Time**: ~200-300 seconds (estimated)
- **Parallelism**: 50 concurrent tasks across all groups
- **Architecture**: Single shared threadpool for all tasks

### Key Optimizations
1. **Upfront CRD Processing**: Eliminates duplicate work
2. **Complete Discovery**: All resources identified before collection starts
3. **Shared Threadpool**: No create/destroy overhead between groups
4. **Granular Tasks**: Small, independent units of work for better parallelism

## References

- [CRD Processor Documentation](common/crd_processor.md) - Technical details on printer column extraction
- [Collection Plan](collection_plan.py) - Data structures for organizing collection tasks
- [Parallel Executor](parallel_executor.py) - Shared threadpool execution engine