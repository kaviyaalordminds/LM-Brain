from typing import List, Optional

from executive_twins.schemas.common import FailureState, SecurityContext
from executive_twins.schemas.specialist import SpecialistMetadata


class SecurityGuardException(Exception):
    """Exception raised when an unauthorized direct execution is attempted by an Executive Twin."""
    pass


class SecurityGuard:
    """
    Security Guardrail Layer.
    Executive Twins NEVER directly execute shell commands, filesystem mutations, or raw system code.
    They may only request authorized specialist delegations through the authorized execution boundary.
    """

    @staticmethod
    def validate_twin_action(action_type: str) -> None:
        """
        Verify that an Executive Twin is not attempting direct shell or privileged execution.
        """
        forbidden = ["shell_exec", "file_write", "system_call", "eval", "code_execution"]
        if action_type.lower() in forbidden:
            raise SecurityGuardException(
                f"SECURITY_AUTHORIZATION_REQUIRED: Executive Twins are forbidden from direct action type '{action_type}'. "
                "Execution must occur via authorized Specialist Agents."
            )

    @staticmethod
    def validate_specialist_tool_authorization(
        specialist: SpecialistMetadata,
        requested_tools: List[str],
        security_context: SecurityContext,
    ) -> Optional[FailureState]:
        """
        Verify that a specialist agent is authorized to use requested tools and meets security context.
        """
        if not security_context.is_authenticated:
            return FailureState.AUTHORIZATION_DENIED

        for tool in requested_tools:
            if tool not in specialist.authorized_tools:
                return FailureState.AUTHORIZATION_DENIED

        return None
