"""
Tests for permission policy.

Covers:
  - Permission.has()
  - Permission.require() enforcement
  - Permission.require_any()
  - ADMIN implies all permissions
  - Standard policies per agent type
  - No agent gets ADMIN by default
  - Tool execution gated by permission
"""

from __future__ import annotations

import pytest

from specialist_agent.core.errors import PermissionDeniedError
from specialist_agent.permissions.policy import (
    Permission,
    PermissionPolicy,
    STANDARD_POLICIES,
    build_policy,
)
from specialist_agent.tools.registry import ToolRegistry
from specialist_agent.tools.filesystem import FilesystemTool
from specialist_agent.tools.shell import ShellTool


class TestPermissionPolicy:
    def _make_policy(self, *perms: Permission) -> PermissionPolicy:
        return PermissionPolicy(agent_id="test-agent", permissions=perms)

    def test_has_permission_true(self):
        policy = self._make_policy(Permission.READ, Permission.WRITE)
        assert policy.has(Permission.READ) is True
        assert policy.has(Permission.WRITE) is True

    def test_has_permission_false(self):
        policy = self._make_policy(Permission.READ)
        assert policy.has(Permission.WRITE) is False

    def test_admin_implies_all(self):
        policy = self._make_policy(Permission.ADMIN)
        for perm in Permission:
            assert policy.has(perm) is True

    def test_require_passes(self):
        policy = self._make_policy(Permission.READ)
        policy.require(Permission.READ)   # Should not raise

    def test_require_raises_on_missing(self):
        policy = self._make_policy(Permission.READ)
        with pytest.raises(PermissionDeniedError) as exc_info:
            policy.require(Permission.WRITE)
        assert "WRITE" in str(exc_info.value)

    def test_require_includes_resource(self):
        policy = self._make_policy(Permission.READ)
        with pytest.raises(PermissionDeniedError) as exc_info:
            policy.require(Permission.EXECUTE, resource="shell")
        assert "shell" in str(exc_info.value)

    def test_require_any_passes_if_one_held(self):
        policy = self._make_policy(Permission.NETWORK)
        policy.require_any(Permission.NETWORK, Permission.ADMIN)   # Should not raise

    def test_require_any_raises_if_none_held(self):
        policy = self._make_policy(Permission.READ)
        with pytest.raises(PermissionDeniedError):
            policy.require_any(Permission.EXECUTE, Permission.ADMIN)

    def test_has_all(self):
        policy = self._make_policy(Permission.READ, Permission.WRITE)
        assert policy.has_all(Permission.READ, Permission.WRITE) is True
        assert policy.has_all(Permission.READ, Permission.EXECUTE) is False

    def test_has_any(self):
        policy = self._make_policy(Permission.READ)
        assert policy.has_any(Permission.READ, Permission.WRITE) is True
        assert policy.has_any(Permission.EXECUTE, Permission.ADMIN) is False

    def test_permissions_are_immutable(self):
        policy = self._make_policy(Permission.READ)
        # frozenset — no way to add permissions after construction
        assert isinstance(policy.permissions, frozenset)


class TestStandardPolicies:
    """Test that standard policies match the specification."""

    def test_no_agent_has_admin(self):
        for agent_type, perms in STANDARD_POLICIES.items():
            assert Permission.ADMIN not in perms, (
                f"Agent '{agent_type}' should NOT have ADMIN permission"
            )

    def test_security_agent_has_only_read_audit_write_artifact(self):
        perms = set(STANDARD_POLICIES["security"])
        assert Permission.READ in perms
        assert Permission.AUDIT in perms
        assert Permission.WRITE_ARTIFACT in perms
        assert Permission.EXECUTE not in perms
        assert Permission.WRITE not in perms

    def test_image_agent_has_read_and_write_artifact(self):
        perms = set(STANDARD_POLICIES["image_generation"])
        assert Permission.READ in perms
        assert Permission.WRITE_ARTIFACT in perms
        assert Permission.ADMIN not in perms

    def test_research_agent_cannot_write(self):
        """Research agent must not have WRITE — it cannot write to Obsidian."""
        perms = set(STANDARD_POLICIES["research"])
        assert Permission.WRITE not in perms, (
            "Research agent must NOT have WRITE permission — cannot write directly to Obsidian"
        )

    def test_backend_agent_has_execute(self):
        perms = set(STANDARD_POLICIES["backend"])
        assert Permission.EXECUTE in perms

    def test_all_ten_types_in_standard_policies(self):
        expected_types = {
            "web_development", "image_generation", "backend", "database",
            "api_integration", "security", "testing", "devops", "ai_ml", "research",
        }
        assert expected_types == set(STANDARD_POLICIES.keys())


class TestBuildPolicy:
    def test_builds_policy_for_known_type(self):
        policy = build_policy("agent-1", "security")
        assert policy.has(Permission.READ)
        assert policy.has(Permission.AUDIT)
        assert not policy.has(Permission.EXECUTE)

    def test_unknown_type_gets_read_only(self):
        policy = build_policy("agent-1", "unknown_type")
        assert policy.has(Permission.READ)
        assert not policy.has(Permission.WRITE)


class TestToolRegistryPermissionEnforcement:
    """Verify that tool registry checks permissions before executing."""

    def test_execute_tool_blocked_without_permission(self):
        registry = ToolRegistry()
        registry.register(ShellTool())
        read_only_policy = PermissionPolicy(
            agent_id="readonly-agent",
            permissions=[Permission.READ],
        )
        result = registry.execute("shell", policy=read_only_policy, command="echo hello")
        assert not result.success
        assert "EXECUTE" in (result.error or "")

    def test_execute_tool_allowed_with_permission(self):
        registry = ToolRegistry()
        registry.register(FilesystemTool())
        policy = PermissionPolicy(
            agent_id="reader-agent",
            permissions=[Permission.READ],
        )
        # exists action only reads — should succeed
        result = registry.execute("filesystem", policy=policy, action="exists", path="/")
        assert result.success

    def test_tool_not_found_returns_failure(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent_tool")
        assert not result.success
        assert "not found" in (result.error or "").lower()
