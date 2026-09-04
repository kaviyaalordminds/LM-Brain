import pytest
from executive_twins.execution.security_guard import SecurityGuard, SecurityGuardException
from executive_twins.schemas.common import FailureState, SecurityContext, SpecialistStatus
from executive_twins.schemas.specialist import Capability, SpecialistMetadata


def test_security_guard_blocks_direct_twin_shell_execution() -> None:
    with pytest.raises(SecurityGuardException) as exc_info:
        SecurityGuard.validate_twin_action("shell_exec")

    assert "SECURITY_AUTHORIZATION_REQUIRED" in str(exc_info.value)


def test_security_guard_blocks_unauthorized_specialist_tool() -> None:
    spec = SpecialistMetadata(
        specialist_id="spec-1",
        name="Design Spec",
        capabilities=[Capability(name="design", description="UI")],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["figma_api"],
    )

    unauth_context = SecurityContext(is_authenticated=False)
    state = SecurityGuard.validate_specialist_tool_authorization(
        spec, ["bash_shell"], unauth_context
    )
    assert state == FailureState.AUTHORIZATION_DENIED

    auth_context = SecurityContext(is_authenticated=True)
    state_unauth_tool = SecurityGuard.validate_specialist_tool_authorization(
        spec, ["bash_shell"], auth_context
    )
    assert state_unauth_tool == FailureState.AUTHORIZATION_DENIED
