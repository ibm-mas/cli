# Parallel Collection Optimization Plan

**Date**: 2026-06-08
**Status**: Future Investigation
**Objective**: Optimize must-gather collection performance by using a single shared threadpool for all collection tasks while maintaining clean sequential UI presentation.

## Current Architecture

### Performance Baseline
- **Total Time**: 568 seconds for full collection
- **Architecture**: Sequential collection groups with parallel tasks within each group
- **Threadpool Strategy**: New threadpool per collection group (OCP, Dependencies, MAS, etc.)

### Current Flow
1. Collect OCP resources (42s) - 4 tasks in sequence
2. Collect Dependencies (122s) - 7 dependency types, each with 4 sub-tasks
3. Collect SLS (15s) - Discovery + namespace collection
4. Collect MAS (279s) - Discovery + per-instance/app collection
5. Collect AI Service - Discovery + collection
6. Generate summaries and archive (30s)

### Current Limitations
- **Sequential Groups**: Each major section waits for previous to complete
- **Idle Threads**: Threadpool created/destroyed for each group
- **Discovery Blocking**: Discovery must complete before collection starts
- **Underutilized Parallelism**: Only ~10-20 threads active at once, could support 50+

## Proposed Architecture

### Two-Phase Approach

#### Phase 1: Discovery & Task Generation (< 5 seconds)
Fast discovery phase that:
- Makes lightweight API calls to discover namespaces
- Identifies all MAS instances and applications
- Generates complete collection plan with all tasks defined
- Does NOT collect any actual data

```python
def planCollection(self, parsedArgs):
    """Discover all resources and generate collection plan."""

    with Halo(text="Discovering resources to collect", spinner=self.spinner) as h:
        plan = CollectionPlan()

        # OCP Discovery
        if not parsedArgs.no_ocp:
            plan.add_group("OCP", [
                ("cluster_resources", ocp.collectClusterResources, args...),
                ("nodes", ocp.collectNodes, args...),
                ("airgap", ocp.collectAirgapResources, args...),
                ("marketplace", ocp.collectMarketplaceResources, args...)
            ])

        # Dependencies Discovery
        if not parsedArgs.no_dependencies:
            # Discover all dependency namespaces upfront
            kafkaNamespaces = discoverNamespacesFromCR(dynClient, "Kafka")
            mongoNamespaces = discoverNamespacesFromCR(dynClient, "MongoDBCommunity")
            db2Namespaces = discoverDb2Namespaces(dynClient, masInstanceIds)
            # ... etc for all dependencies

            # Add collection tasks for each discovered namespace
            for ns in kafkaNamespaces:
                plan.add_group(f"Kafka ({ns})", [
                    ("ibm_resources", collectResourcesParallel, ns, ibmCRDs, ...),
                    ("standard_resources", collectResourcesParallel, ns, standardResources, ...),
                    ("secrets", collectSecrets, ns, ...),
                    ("pods", collectPods, ns, ...)
                ])
            # ... repeat for all dependency types

        # MAS Discovery
        masInstances = mas_core.discoverMASInstances(dynClient, masInstanceIds)
        for instance in masInstances:
            # Add core namespace tasks
            plan.add_group(f"MAS {instance.id} - Core", [...])

            # Add app namespace tasks
            for app in instance.apps:
                plan.add_group(f"MAS {instance.id} - {app}", [...])

        # AI Service Discovery
        aiInstances = aiservice_instance.discoverAIServiceInstances(dynClient)
        for instance in aiInstances:
            plan.add_group(f"AI Service {instance.id}", [...])

        h.stop_and_persist(
            symbol="✅️",
            text=f"Discovered {plan.total_tasks} collection tasks across {plan.total_groups} groups"
        )

    return plan
```

#### Phase 2: Parallel Execution with Sequential Display (200-300s estimated)
Execute all tasks in parallel but display progress sequentially:

```python
def executeCollection(self, plan):
    """Execute all collection tasks in parallel with grouped progress display."""

    # Single massive threadpool - submit ALL tasks immediately
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit every single task to the pool upfront
        all_futures = {}
        for group in plan.groups:
            group_futures = []
            for task_name, func, *args in group.tasks:
                future = executor.submit(func, *args)
                all_futures[future] = (group.name, task_name)
                group_futures.append(future)
            group.futures = group_futures

        # Now show sequential spinners for each group
        # Tasks are already running in background!
        for group in plan.groups:
            self.printH2(group.name)

            # Show spinner for each task type in the group
            for task_name, futures_subset in group.task_groups:
                total = len(futures_subset)
                completed = 0

                with Halo(
                    text=f"Collected {completed}/{total} {task_name}",
                    spinner=self.spinner
                ) as h:
                    # Wait for this subset of futures to complete
                    # Many may already be done by the time we get here!
                    for future in as_completed(futures_subset):
                        try:
                            future.result()
                            completed += 1
                            h.text = f"Collected {completed}/{total} {task_name}"
                        except Exception as e:
                            logger.error(f"Task failed: {e}")
                            completed += 1

                    h.stop_and_persist(
                        symbol="✅️",
                        text=f"Collected {total} {task_name}"
                    )
```

### Key Design Decisions

#### CollectionPlan Class
```python
class CollectionPlan:
    """Represents the complete collection plan with all tasks."""

    def __init__(self):
        self.groups = []  # List of CollectionGroup objects
        self.total_tasks = 0
        self.total_groups = 0

    def add_group(self, name, tasks):
        """Add a collection group with its tasks."""
        group = CollectionGroup(name, tasks)
        self.groups.append(group)
        self.total_tasks += len(tasks)
        self.total_groups += 1

class CollectionGroup:
    """Represents a logical group of collection tasks."""

    def __init__(self, name, tasks):
        self.name = name  # e.g., "Kafka (strimzi)"
        self.tasks = tasks  # List of (task_name, func, *args)
        self.futures = []  # Populated during execution

    @property
    def task_groups(self):
        """Group tasks by type for display (IBM resources, secrets, pods, etc.)."""
        # Returns: [(task_type, [futures])]
        pass
```

#### Discovery Function Refactoring
Current collectors mix discovery and collection. Need to extract:

```python
# BEFORE (current)
def collectKafka(dynClient, outputDir, ...):
    kafkaNamespaces = discoverNamespacesFromCR(dynClient, "Kafka")
    for ns in kafkaNamespaces:
        # Collect resources...

# AFTER (proposed)
def discoverKafkaNamespaces(dynClient):
    """Discover Kafka namespaces without collecting data."""
    return discoverNamespacesFromCR(dynClient, "Kafka")

def generateKafkaCollectionTasks(dynClient, namespace, outputDir, ...):
    """Generate collection tasks for a Kafka namespace."""
    return [
        ("ibm_resources", collectResourcesParallel, dynClient, namespace, ibmCRDs, ...),
        ("standard_resources", collectResourcesParallel, dynClient, namespace, standardResources, ...),
        ("secrets", collectSecrets, dynClient, namespace, ...),
        ("pods", collectPods, dynClient, namespace, ...)
    ]
```

## Expected Benefits

### Performance Improvements
- **Estimated Total Time**: 200-300 seconds (down from 568s)
- **Speedup**: ~2x faster
- **Parallelism**: 50+ concurrent tasks vs current 10-20
- **Idle Time**: Eliminated - all tasks start immediately

### User Experience
- **Same Output Format**: Identical to current sequential display
- **Progress Visibility**: Clear indication of what's being collected
- **Early Feedback**: Discovery phase shows total work upfront
- **No Breaking Changes**: Output format unchanged

### Technical Benefits
- **Resource Efficiency**: Single threadpool, no create/destroy overhead
- **Better CPU Utilization**: More tasks running concurrently
- **Cleaner Architecture**: Separation of discovery and collection
- **Easier Testing**: Can test discovery and execution independently

## Implementation Phases

### Phase 1: Refactor Discovery (Low Risk)
- Extract discovery logic from all collectors
- Create discovery functions that return namespace lists
- No changes to collection logic yet
- **Estimated Effort**: 2-3 days

### Phase 2: Create CollectionPlan Infrastructure (Medium Risk)
- Implement `CollectionPlan` and `CollectionGroup` classes
- Create task generation functions
- Build plan in `planCollection()` method
- **Estimated Effort**: 3-4 days

### Phase 3: Implement Parallel Execution (Medium Risk)
- Implement `executeCollection()` with shared threadpool
- Update progress tracking for sequential display
- Handle error cases and edge conditions
- **Estimated Effort**: 3-4 days

### Phase 4: Testing & Validation (Critical)
- Test with various cluster configurations
- Verify output format matches current implementation
- Performance benchmarking
- Edge case testing (missing namespaces, errors, etc.)
- **Estimated Effort**: 3-5 days

## Risks & Mitigations

### Risk: Increased Memory Usage
- **Impact**: 50+ concurrent tasks may increase memory footprint
- **Mitigation**: Monitor memory usage, adjust max_workers if needed
- **Fallback**: Reduce max_workers to 20-30 if memory constrained

### Risk: API Rate Limiting
- **Impact**: Kubernetes API may throttle with 50+ concurrent requests
- **Mitigation**: Implement backoff/retry logic, adjust max_workers
- **Fallback**: Reduce parallelism if rate limiting detected

### Risk: Complex Error Handling
- **Impact**: Errors in parallel tasks harder to track and report
- **Mitigation**: Comprehensive logging, per-task error tracking
- **Fallback**: Detailed error messages with task context

### Risk: Breaking Changes
- **Impact**: Output format changes could break user scripts/automation
- **Mitigation**: Extensive testing, maintain exact output format
- **Fallback**: Feature flag to enable/disable new architecture

## Testing Strategy

### Unit Tests
- Test discovery functions independently
- Test task generation logic
- Test CollectionPlan class methods
- Test error handling in parallel execution

### Integration Tests
- Test full collection flow with mock cluster
- Test with various namespace configurations
- Test error scenarios (missing resources, API failures)
- Test progress tracking and UI output

### Performance Tests
- Benchmark against current implementation
- Test with different max_workers values
- Monitor memory and CPU usage
- Test with large clusters (many namespaces)

### Regression Tests
- Verify output format matches current implementation
- Verify all resources collected correctly
- Verify error messages unchanged
- Verify archive structure unchanged

## Success Criteria

1. **Performance**: Collection time reduced by at least 30%
2. **Correctness**: All resources collected (verified by diff with current implementation)
3. **Output Format**: Identical output to current implementation
4. **Stability**: No increase in error rates or failures
5. **Memory**: Memory usage within acceptable limits (< 2GB)

## Future Enhancements

### Dynamic Worker Scaling
Adjust max_workers based on:
- Available system resources
- API rate limit detection
- Current task completion rate

### Progress Estimation
Show estimated time remaining based on:
- Historical collection times
- Current completion rate
- Task complexity

### Cancellation Support
Allow user to cancel collection:
- Gracefully stop all running tasks
- Save partial results
- Clean up resources

## References

- Current implementation: [`python/src/mas/cli/must_gather/app.py`](python/src/mas/cli/must_gather/app.py)
- Parallel collection utility: [`python/src/mas/cli/must_gather/common/parallel.py`](python/src/mas/cli/must_gather/common/parallel.py)
- Dependency collectors: [`python/src/mas/cli/must_gather/dependencies/`](python/src/mas/cli/must_gather/dependencies/)