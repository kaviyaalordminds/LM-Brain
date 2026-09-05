"""
DEV/TEST adapters and registered Command Execution capability handlers.
Used for local development and testing without production cloud containers.
"""

from typing import Dict, List, Optional

from executive_twins.command_execution.command_executor import (
    CommandRegistry,
    ControlledCommandExecutor,
)
from executive_twins.command_execution.interfaces import ICommandExecutor
from executive_twins.command_execution.models import (
    CommandRequest,
    CommandResult,
    CommandType,
)
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


class DevCommandExecutorAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Manages ControlledCommandExecutor instances for active workspaces.
    THIS IS NOT THE PRODUCTION SANDBOX CONTAINER INTEGRATION.
    """

    def __init__(
        self,
        workspace_adapter: DevTestWorkspaceAdapter,
        registry: Optional[CommandRegistry] = None,
    ) -> None:
        self.workspace_adapter = workspace_adapter
        self.registry = registry or CommandRegistry()
        self._active_executors: Dict[str, ICommandExecutor] = {}

    def get_executor(self, workspace_id: str) -> Optional[ICommandExecutor]:
        """Get or create a ControlledCommandExecutor for a workspace."""
        if workspace_id in self._active_executors:
            return self._active_executors[workspace_id]

        workspace = self.workspace_adapter.get_workspace(workspace_id)
        if not workspace or not workspace.workspace_exists():
            return None

        executor = ControlledCommandExecutor(
            workspace=workspace, registry=self.registry
        )
        self._active_executors[workspace_id] = executor
        return executor


class BaseCommandCapabilityHandler(BaseCapabilityHandler):
    """
    Abstract base capability handler for controlled workspace command execution.
    """

    command_type: CommandType
    required_tool = "command_executor"
    required_params = ["workspace_id", "executable"]
    allowed_params = [
        "workspace_id",
        "executable",
        "arguments",
        "timeout_seconds",
        "path_arguments",
        "test_suite",
    ]

    def __init__(self, adapter: DevCommandExecutorAdapter) -> None:
        self.adapter = adapter

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        executable = str(request.inputs.get("executable", ""))
        arguments = request.inputs.get("arguments", [])
        if isinstance(arguments, str):
            arguments = arguments.split()
        elif not isinstance(arguments, list):
            arguments = []

        path_arguments = request.inputs.get("path_arguments", [])
        if isinstance(path_arguments, str):
            path_arguments = [path_arguments]
        elif not isinstance(path_arguments, list):
            path_arguments = []

        timeout_sec = float(request.inputs.get("timeout_seconds", 30.0))

        executor = self.adapter.get_executor(ws_id)
        if not executor:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"{self.capability_name.upper()}_FAILED: Workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        cmd_req = CommandRequest(
            command_type=self.command_type,
            executable=executable,
            arguments=arguments,
            workspace_id=ws_id,
            timeout_seconds=timeout_sec,
            path_arguments=path_arguments,
        )

        res: CommandResult = executor.execute(cmd_req)
        if not res.success:
            err_msg = res.error_message or f"Execution failed with status '{res.status.value}'"
            err_output = f"{self.capability_name.upper()}_FAILED: {err_msg}"
            if res.stderr:
                err_output += f"\nStderr:\n{res.stderr}"
            return CapabilityHandlerOutput(
                success=False,
                output_text=err_output,
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        output_msg = res.stdout if res.stdout else f"Command '{executable}' completed successfully."
        return CapabilityHandlerOutput(
            success=True,
            output_text=output_msg,
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class BuildCapabilityHandler(BaseCommandCapabilityHandler):
    """Approved Capability Execution Handler for workspace build commands."""
    capability_name = "build_command_execution"
    command_type = CommandType.BUILD


class TestCapabilityHandler(BaseCommandCapabilityHandler):
    """Approved Capability Execution Handler for workspace test commands."""
    __test__ = False  # Prevent pytest from collecting this as a test class
    capability_name = "test_command_execution"
    command_type = CommandType.TEST


class LintCapabilityHandler(BaseCommandCapabilityHandler):
    """Approved Capability Execution Handler for workspace lint commands."""
    capability_name = "lint_command_execution"
    command_type = CommandType.LINT


class TypecheckCapabilityHandler(BaseCommandCapabilityHandler):
    """Approved Capability Execution Handler for workspace typecheck commands."""
    capability_name = "typecheck_command_execution"
    command_type = CommandType.TYPECHECK
