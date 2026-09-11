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
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
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
from executive_twins.reasoning.interfaces import IReasoningModel
from executive_twins.reasoning.models import ReasoningConfig
from executive_twins.reasoning.reasoning_service import ReasoningService
from executive_twins.schemas.common import FactItem, FactState, SecurityContext, SpecialistStatus
from executive_twins.schemas.knowledge import ObsidianDocument
from executive_twins.schemas.specialist import (
    Capability,
    CapabilityRequirement,
    RegistryProvenance,
    SpecialistMetadata,
)
from executive_twins.software_development.dev_adapters import (
    DevTestSoftwareDevelopmentAdapter,
    create_software_development_specialist,
)
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


class DevTestMasterOrchestratorFactory:
    """
    Factory to construct fully wired, deterministic Master Orchestrator instances for tests and local development.
    """

    @classmethod
    def create_default_test_orchestrator(
        cls,
        config: Optional[OrchestrationConfig] = None,
        reasoning_adapter: Optional[IReasoningModel] = None,
        agent_adapter: Optional[ISpecialistAgentAdapter] = None,
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
                    Capability(name="project_validation", description="Validate project files"),
                    Capability(name="software_validation", description="Validate software files"),
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

    @classmethod
    def create_local_development_orchestrator(
        cls,
        config: Optional[OrchestrationConfig] = None,
        base_workspace_dir: Optional[str] = None,
        reasoning_adapter: Optional[IReasoningModel] = None,
        include_knowledge: bool = True,
        include_twins: bool = True,
    ) -> MasterOrchestrator:
        """
        Factory constructing a production-grade local development MasterOrchestrator
        with real FileService, Workspace, Command Execution, and SpecialistExecutionEngine boundaries.
        Persists workspaces in the repository workspaces root by default.
        """
        cfg = config or OrchestrationConfig()

        # 1. Workspace Adapter & Dev Adapter
        ws_adapter = DevTestWorkspaceAdapter(base_temp_dir=base_workspace_dir)
        dev_adapter = DevTestSoftwareDevelopmentAdapter(
            base_temp_dir=ws_adapter.base_temp_dir,
            use_mock_docker=True,
        )
        ws_adapter.create_workspace("default")

        # 2. Specialist Registry
        registry = InMemorySpecialistRegistryAdapter()
        spec = create_software_development_specialist("spec_software_dev_01")
        registry.register_specialist(spec)

        # 3. Specialist Execution Engine with all real handlers registered
        execution_engine = SpecialistExecutionEngine(registry_client=registry)
        dev_adapter.register_all_handlers(execution_engine)

        agent_adapter = SpecialistExecutionAdapter(execution_engine=execution_engine)

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
            # Seed approved company knowledge
            approved_doc = ObsidianDocument(
                document_id="doc_company_profile",
                vault_path="company_knowledge/default/company_profile.md",
                title="Company Profile and Approved Information",
                content="NovaPulse Robotics provides autonomous warehouse robotics solutions.\nServices: Fleet Orchestrator, Autonomous AMR-500, Cloud Telemetry API.\nContact: contact@novapulse.io",
                facts=[
                    FactItem(statement="Company name: NovaPulse Robotics", state=FactState.FACT, source="obsidian_vault"),
                    FactItem(statement="Mission: Autonomous warehouse robotics solutions", state=FactState.FACT, source="obsidian_vault"),
                    FactItem(statement="Core products: Fleet Orchestrator, Autonomous AMR-500, Cloud Telemetry API", state=FactState.FACT, source="obsidian_vault"),
                    FactItem(statement="Contact: contact@novapulse.io", state=FactState.FACT, source="obsidian_vault"),
                ],
                confidence=1.0,
            )
            obs_adapter.seed_document(approved_doc)

        # 5. Reasoning Service
        r_adapter = reasoning_adapter or DevTestReasoningAdapter()
        reasoning_service = ReasoningService(
            model_adapter=r_adapter,
            knowledge_layer=knowledge_layer,
            config=ReasoningConfig(timeout_seconds=getattr(r_adapter, "timeout", 60.0)),
        )

        # 6. Twin Orchestrator
        twin_orch = None
        if include_twins:
            twin_orch = TwinOrchestrator(
                registry_client=registry,
                agent_adapter=agent_adapter,
            )

        # 7. Master Orchestrator
        return MasterOrchestrator(
            reasoning_service=reasoning_service,
            registry_client=registry,
            agent_adapter=agent_adapter,
            knowledge_layer=knowledge_layer,
            twin_orchestrator=twin_orch,
            config=cfg,
            perception_engine=StandardPerceptionEngine(),
            writeback_handler=StandardMemoryWritebackHandler(knowledge_layer),
        )
