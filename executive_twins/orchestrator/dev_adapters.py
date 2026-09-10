"""
Deterministic Development and Test Adapters for Master Orchestrator.
Enables 100% offline, reproducible testing of the full autonomous control loop without external API dependencies.
"""

from typing import Any, Dict, List, Optional
import uuid

from executive_twins.client.agent_adapter import (
    ISpecialistAgentAdapter,
    MockSpecialistAgentAdapter,
)
from executive_twins.client.registry_client import (
    ISpecialistRegistryClient,
    InMemorySpecialistRegistryAdapter,
)
from executive_twins.memory.dev_adapters import (
    DevTestClaudeClient,
    DevTestMemoryKnowledgeAgent,
    DevTestObsidianAdapter,
)
from executive_twins.memory.knowledge_layer import CompanyKnowledgeService
from executive_twins.orchestrator.control_loop import (
    AutonomousControlLoop,
    StandardMemoryWritebackHandler,
    StandardPerceptionEngine,
)
from executive_twins.orchestrator.master_orchestrator import MasterOrchestrator
from executive_twins.orchestrator.models import OrchestrationConfig
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.reasoning.dev_adapters import DevTestReasoningAdapter
from executive_twins.reasoning.reasoning_service import ReasoningService
from executive_twins.schemas.common import SecurityContext, SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    CapabilityRequirement,
    RegistryProvenance,
    SpecialistMetadata,
)


class DevTestMasterOrchestratorFactory:
    """
    Factory to construct fully wired, deterministic Master Orchestrator instances for tests and local development.
    """

    @classmethod
    def create_default_test_orchestrator(
        cls,
        config: Optional[OrchestrationConfig] = None,
        reasoning_adapter: Optional[DevTestReasoningAdapter] = None,
        agent_adapter: Optional[MockSpecialistAgentAdapter] = None,
        registry_client: Optional[ISpecialistRegistryClient] = None,
        include_knowledge: bool = True,
        include_twins: bool = True,
    ) -> MasterOrchestrator:
        cfg = config or OrchestrationConfig()

        # 1. Reasoning Service
        r_adapter = reasoning_adapter or DevTestReasoningAdapter()
        reasoning_service = ReasoningService(model_adapter=r_adapter)

        # 2. Specialist Registry
        if registry_client is None:
            mock_registry = InMemorySpecialistRegistryAdapter()
            # Seed default specialists for standard capabilities
            dev_spec = SpecialistMetadata(
                specialist_id="spec_software_dev_01",
                name="Software Development Specialist",
                capabilities=[
                    Capability(name="file_list", description="List workspace files"),
                    Capability(name="file_create", description="Create workspace files"),
                    Capability(name="file_read", description="Read workspace files"),
                    Capability(name="file_update", description="Update workspace files"),
                    Capability(name="file_delete", description="Delete workspace files"),
                    Capability(name="test_command_execution", description="Run tests"),
                    Capability(name="build_command_execution", description="Run build"),
                    Capability(name="inspect", description="Inspect project"),
                    Capability(name="marketing_strategy", description="Marketing campaign strategy"),
                    Capability(name="visual_design", description="Visual design creation"),
                    Capability(name="copywriting", description="Ad copy and messaging"),
                ],
                status=SpecialistStatus.ACTIVE,
                provenance=RegistryProvenance(registry_id="test-reg-01", snapshot_id="snap-01"),
            )
            mock_registry.register_specialist(dev_spec)
            registry_client = mock_registry

        # 3. Specialist Agent Adapter
        a_adapter = agent_adapter or MockSpecialistAgentAdapter()

        # 4. Knowledge Layer
        knowledge_layer = None
        if include_knowledge:
            obs_adapter = DevTestObsidianAdapter()
            claude_client = DevTestClaudeClient()
            mem_agent = DevTestMemoryKnowledgeAgent(claude_client=claude_client)
            knowledge_layer = CompanyKnowledgeService(
                obsidian_adapter=obs_adapter,
                memory_agent=mem_agent,
            )

        # 5. Twin Orchestrator
        twin_orch = None
        if include_twins:
            twin_orch = TwinOrchestrator(
                registry_client=registry_client,
                agent_adapter=a_adapter,
            )

        # 6. Master Orchestrator
        return MasterOrchestrator(
            reasoning_service=reasoning_service,
            registry_client=registry_client,
            agent_adapter=a_adapter,
            knowledge_layer=knowledge_layer,
            twin_orchestrator=twin_orch,
            config=cfg,
            perception_engine=StandardPerceptionEngine(),
            writeback_handler=StandardMemoryWritebackHandler(knowledge_layer),
        )
