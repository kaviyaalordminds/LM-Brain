"""
Specialist Agent — Permission Policy

Defines the Permission enum and PermissionPolicy class.

Every Specialist Agent is assigned a PermissionPolicy at construction.
All tool executions are checked against the policy before proceeding.

Permission levels (ascending privilege):
  READ             — read-only access to data/files
  WRITE            — create/modify files and non-destructive resources
  WRITE_ARTIFACT   — specifically allowed to produce output artifacts
  EXECUTE          — run commands, scripts, or processes
  NETWORK          — HTTP/external network calls
  DATABASE         — database read/write
  AUDIT            — security audit access (read + structured reporting)
  ADMIN            — unrestricted (reserved, not granted to any specialist by default)
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from specialist_agent.core.errors import PermissionDeniedError


class Permission(str, Enum):
    """Permission levels for tool and resource access."""

    READ = "READ"
    WRITE = "WRITE"
    WRITE_ARTIFACT = "WRITE_ARTIFACT"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    AUDIT = "AUDIT"
    ADMIN = "ADMIN"


class PermissionPolicy:
    """
    Immutable permission set assigned to a single agent.

    Rules
    -----
    - ADMIN implies all permissions.
    - Permission checks happen BEFORE any tool execution.
    - Denial raises PermissionDeniedError (never silently skips).
    - Policies are constructed at agent spawn time and cannot be mutated.
    """

    def __init__(self, agent_id: str, permissions: Iterable[Permission]) -> None:
        self._agent_id = agent_id
        # Freeze the permission set at construction time
        self._permissions: frozenset[Permission] = frozenset(permissions)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def permissions(self) -> frozenset[Permission]:
        return self._permissions

    def has(self, permission: Permission) -> bool:
        """Return True if the agent holds *permission* (ADMIN implies all)."""
        return Permission.ADMIN in self._permissions or permission in self._permissions

    def has_all(self, *permissions: Permission) -> bool:
        """Return True if the agent holds ALL of the given permissions."""
        return all(self.has(p) for p in permissions)

    def has_any(self, *permissions: Permission) -> bool:
        """Return True if the agent holds at least one of the given permissions."""
        return any(self.has(p) for p in permissions)

    # ------------------------------------------------------------------
    # Enforcement API
    # ------------------------------------------------------------------

    def require(self, permission: Permission, resource: str | None = None) -> None:
        """
        Raise PermissionDeniedError if the agent does not hold *permission*.

        Called by the tool registry before every tool execution.
        """
        if not self.has(permission):
            raise PermissionDeniedError(
                agent_id=self._agent_id,
                permission=permission.value,
                resource=resource,
            )

    def require_any(self, *permissions: Permission, resource: str | None = None) -> None:
        """Raise PermissionDeniedError if NONE of the given permissions are held."""
        if not self.has_any(*permissions):
            perm_str = " | ".join(p.value for p in permissions)
            raise PermissionDeniedError(
                agent_id=self._agent_id,
                permission=f"any_of({perm_str})",
                resource=resource,
            )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        perms = sorted(p.value for p in self._permissions)
        return f"PermissionPolicy(agent_id={self._agent_id!r}, permissions={perms})"


# ─────────────────────────────────────────────────────────────────────────────
# Standard permission sets for each specialist type
# ─────────────────────────────────────────────────────────────────────────────

STANDARD_POLICIES: dict[str, list[Permission]] = {
    "web_development": [
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.NETWORK,
    ],
    "image_generation": [
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    "backend": [
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.DATABASE,
        Permission.NETWORK,
    ],
    "database": [
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.DATABASE,
    ],
    "api_integration": [
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    "security": [
        Permission.READ,
        Permission.AUDIT,
        Permission.WRITE_ARTIFACT,
    ],
    "testing": [
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        Permission.NETWORK,
    ],
    "devops": [
        Permission.READ,
        Permission.WRITE,
        Permission.WRITE_ARTIFACT,
        Permission.EXECUTE,
        # NOTE: ADMIN is NOT granted — no unrestricted destructive access.
    ],
    "ai_ml": [
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
    ],
    "research": [
        Permission.READ,
        Permission.WRITE_ARTIFACT,
        Permission.NETWORK,
        # NOTE: WRITE is NOT granted — research agent cannot write to Obsidian.
    ],
}


def build_policy(agent_id: str, agent_type: str) -> PermissionPolicy:
    """
    Build a PermissionPolicy for the given agent type.

    Falls back to READ-only if agent_type is unknown.
    """
    perms = STANDARD_POLICIES.get(agent_type, [Permission.READ])
    return PermissionPolicy(agent_id=agent_id, permissions=perms)
