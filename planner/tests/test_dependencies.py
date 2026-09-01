"""
Tests for Dependency Graph, Cycle Detection, Topological Sort, and Parallel Groups.
"""
from __future__ import annotations

import pytest

from app.core.dependency_graph import build_dependency_graph, DependencyGraphResult


class TestDependencyGraph:
    def test_single_step_no_dependencies(self):
        res = build_dependency_graph(["step-01-web_development"], explicit_dependencies={"step-01-web_development": []})
        assert res.valid is True
        assert res.execution_order == ["step-01-web_development"]
        assert res.parallel_groups == [["step-01-web_development"]]

    def test_linear_dependency_chain(self):
        steps = ["step-01-database", "step-02-backend", "step-03-testing"]
        deps = {
            "step-01-database": [],
            "step-02-backend": ["step-01-database"],
            "step-03-testing": ["step-02-backend"],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is True
        assert res.execution_order == ["step-01-database", "step-02-backend", "step-03-testing"]
        assert len(res.parallel_groups) == 3
        assert res.parallel_groups[0] == ["step-01-database"]
        assert res.parallel_groups[1] == ["step-02-backend"]
        assert res.parallel_groups[2] == ["step-03-testing"]

    def test_diamond_dependency_graph(self):
        # B depends on A; C depends on A; D depends on B and C
        steps = ["step-A", "step-B", "step-C", "step-D"]
        deps = {
            "step-A": [],
            "step-B": ["step-A"],
            "step-C": ["step-A"],
            "step-D": ["step-B", "step-C"],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is True
        assert res.execution_order[0] == "step-A"
        assert res.execution_order[-1] == "step-D"
        # B and C should be in parallel group 1
        assert len(res.parallel_groups) == 3
        assert res.parallel_groups[0] == ["step-A"]
        assert set(res.parallel_groups[1]) == {"step-B", "step-C"}
        assert res.parallel_groups[2] == ["step-D"]

    def test_independent_parallel_tasks(self):
        steps = ["step-01-database", "step-02-web_development"]
        deps = {
            "step-01-database": [],
            "step-02-web_development": [],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is True
        assert len(res.parallel_groups) == 1
        assert set(res.parallel_groups[0]) == {"step-01-database", "step-02-web_development"}

    def test_two_node_cycle_rejected(self):
        steps = ["step-A", "step-B"]
        deps = {
            "step-A": ["step-B"],
            "step-B": ["step-A"],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is False
        assert any("Circular dependency" in err for err in res.errors)

    def test_three_node_cycle_rejected(self):
        steps = ["step-A", "step-B", "step-C"]
        deps = {
            "step-A": ["step-C"],
            "step-B": ["step-A"],
            "step-C": ["step-B"],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is False
        assert any("Circular dependency" in err for err in res.errors)

    def test_self_cycle_rejected(self):
        steps = ["step-A"]
        deps = {"step-A": ["step-A"]}
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is False
        assert any("Circular dependency" in err for err in res.errors)

    def test_nonexistent_dependency_rejected(self):
        steps = ["step-A"]
        deps = {"step-A": ["step-GHOST"]}
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is False
        assert any("non-existent dependency 'step-GHOST'" in err for err in res.errors)

    def test_duplicate_dependencies_rejected(self):
        steps = ["step-A", "step-B"]
        deps = {
            "step-A": [],
            "step-B": ["step-A", "step-A"],
        }
        res = build_dependency_graph(steps, explicit_dependencies=deps)
        assert res.valid is False
        assert any("duplicate dependency" in err for err in res.errors)

    def test_natural_dependencies_inferred(self):
        steps = ["step-01-database", "step-02-backend", "step-03-testing"]
        res = build_dependency_graph(steps)
        assert res.valid is True
        assert len(res.execution_order) == 3
