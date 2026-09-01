"""
Planner — Dependency Graph

Builds and validates a DAG (Directed Acyclic Graph) over plan steps.
Provides:
  - Dependency validation (all IDs exist)
  - Cycle detection (DFS-based)
  - Topological sort (Kahn's algorithm — deterministic)
  - Parallel group resolution (level-based BFS)

This module does NOT execute any steps. It only analyzes structure.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class DependencyGraphResult:
    """Result of dependency graph analysis."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)   # Topological order
    parallel_groups: list[list[str]] = field(default_factory=list)  # Concurrent waves
    dependencies: dict[str, list[str]] = field(default_factory=dict)  # step_id → deps


def _build_natural_dependencies(step_ids: list[str]) -> dict[str, list[str]]:
    """
    Build natural dependency chain based on specialist ordering.
    If no explicit dependencies are supplied, the planner infers a natural
    dependency order from the specialist type embedded in step IDs.
    """
    # Natural ordering: research → database → backend → api_integration →
    #                   security → web_development → ai_ml → image_generation →
    #                   testing → devops
    NATURAL_ORDER = [
        "research", "database", "backend", "api_integration",
        "security", "web_development", "ai_ml", "image_generation",
        "testing", "devops",
    ]

    def _specialist(step_id: str) -> str:
        """Extract specialist suffix from step-01-backend style IDs."""
        parts = step_id.split("-", 2)
        return parts[2] if len(parts) == 3 else step_id

    ordered_steps = sorted(
        step_ids,
        key=lambda sid: (
            NATURAL_ORDER.index(_specialist(sid))
            if _specialist(sid) in NATURAL_ORDER
            else len(NATURAL_ORDER)
        ),
    )

    deps: dict[str, list[str]] = {sid: [] for sid in step_ids}

    # Steps that are independent of each other (parallel-friendly)
    PARALLEL_SAFE = {
        frozenset({"database", "web_development"}),
    }

    for i, sid in enumerate(ordered_steps):
        spec = _specialist(sid)
        # Find the closest predecessor by natural order that is NOT parallel-safe
        for pred_sid in reversed(ordered_steps[:i]):
            pred_spec = _specialist(pred_sid)
            pair = frozenset({spec, pred_spec})
            if pair not in PARALLEL_SAFE:
                deps[sid] = [pred_sid]
                break

    return deps


def build_dependency_graph(
    step_ids: list[str],
    explicit_dependencies: dict[str, list[str]] | None = None,
) -> DependencyGraphResult:
    """
    Build and validate the dependency graph.

    Args:
        step_ids: All step IDs in the plan.
        explicit_dependencies: Optional caller-supplied dependency overrides.
            If None, natural ordering is inferred.

    Returns:
        DependencyGraphResult with validation status, topological order,
        and parallel groups.
    """
    errors: list[str] = []
    id_set = set(step_ids)

    if explicit_dependencies is not None:
        deps = {sid: list(dep_ids) for sid, dep_ids in explicit_dependencies.items()}
        # Ensure all step_ids have an entry
        for sid in step_ids:
            deps.setdefault(sid, [])
    else:
        deps = _build_natural_dependencies(step_ids)

    # ------------------------------------------------------------------
    # 1. Validate dependency references
    # ------------------------------------------------------------------
    for sid, dep_ids in deps.items():
        if sid not in id_set:
            errors.append(f"Step '{sid}' in dependency map does not exist in plan.")
        for dep_id in dep_ids:
            if dep_id not in id_set:
                errors.append(
                    f"Step '{sid}' references non-existent dependency '{dep_id}'."
                )

    # ------------------------------------------------------------------
    # 2. Duplicate dependency check
    # ------------------------------------------------------------------
    for sid, dep_ids in deps.items():
        if len(dep_ids) != len(set(dep_ids)):
            errors.append(f"Step '{sid}' has duplicate dependency entries.")

    if errors:
        return DependencyGraphResult(valid=False, errors=errors, dependencies=deps)

    # ------------------------------------------------------------------
    # 3. Cycle detection — DFS-based (also validates graph structure)
    # ------------------------------------------------------------------
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {sid: WHITE for sid in step_ids}
    cycle_errors: list[str] = []

    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        for neighbour in deps.get(node, []):
            if color[neighbour] == GRAY:
                cycle_path = " → ".join(path + [neighbour])
                cycle_errors.append(f"Circular dependency detected: {cycle_path}")
                return
            if color[neighbour] == WHITE:
                dfs(neighbour, path + [neighbour])
        color[node] = BLACK

    for sid in step_ids:
        if color[sid] == WHITE:
            dfs(sid, [sid])

    if cycle_errors:
        errors.extend(cycle_errors)
        return DependencyGraphResult(valid=False, errors=errors, dependencies=deps)

    # ------------------------------------------------------------------
    # 4. Topological sort — Kahn's algorithm (deterministic via sorted queues)
    # ------------------------------------------------------------------
    in_degree: dict[str, int] = defaultdict(int)
    successors: dict[str, list[str]] = defaultdict(list)

    for sid in step_ids:
        in_degree.setdefault(sid, 0)
        for dep_id in deps.get(sid, []):
            in_degree[dep_id] = in_degree.get(dep_id, 0)
            successors[dep_id].append(sid)

    # Initial zero-in-degree nodes (sorted for determinism)
    queue: deque[str] = deque(sorted(s for s in step_ids if in_degree[s] == 0))
    topo_order: list[str] = []

    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for succ in sorted(successors[node]):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    if len(topo_order) != len(step_ids):
        errors.append("Topological sort incomplete — unresolvable cycle present.")
        return DependencyGraphResult(valid=False, errors=errors, dependencies=deps)

    # ------------------------------------------------------------------
    # 5. Parallel groups — level-based BFS
    # ------------------------------------------------------------------
    # Assign each node to the earliest level where all its dependencies
    # have been assigned to a strictly earlier level.
    level: dict[str, int] = {}
    for sid in topo_order:
        dep_levels = [level[d] for d in deps.get(sid, []) if d in level]
        level[sid] = (max(dep_levels) + 1) if dep_levels else 0

    max_level = max(level.values(), default=0)
    parallel_groups: list[list[str]] = []
    for lv in range(max_level + 1):
        group = sorted(sid for sid, lvl in level.items() if lvl == lv)
        if group:
            parallel_groups.append(group)

    return DependencyGraphResult(
        valid=True,
        errors=[],
        execution_order=topo_order,
        parallel_groups=parallel_groups,
        dependencies=deps,
    )
