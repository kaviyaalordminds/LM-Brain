"""
Master Orchestrator implementation for Autonomous AI Workforce.
Coordinates high-level perception, knowledge retrieval, reasoning, capability selection,
specialist delegation, verification, failure recovery, and memory writeback.
"""

from typing import Optional

from executive_twins.client.agent_adapter import ISpecialistAgentAdapter
from executive_twins.client.registry_client import ISpecialistRegistryClient
from executive_twins.memory.interfaces import IKnowledgeMemoryLayer
from executive_twins.orchestrator.control_loop import (
    AutonomousControlLoop,
    StandardMemoryWritebackHandler,
    StandardPerceptionEngine,
)
from executive_twins.orchestrator.interfaces import (
    IControlLoop,
    IMasterOrchestrator,
    IMemoryWritebackHandler,
    IPerceptionEngine,
)
from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
)
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.reasoning.interfaces import IReasoningService


class MasterOrchestrator(IMasterOrchestrator):
    """
    Authoritative Master Orchestrator coordinating workforce tasks.
    Operates strictly as a workflow coordinator above existing specialist execution,
    reasoning, knowledge, and executive twin layers.
    """

    def __init__(
        self,
        reasoning_service: IReasoningService,
        registry_client: ISpecialistRegistryClient,
        agent_adapter: ISpecialistAgentAdapter,
        knowledge_layer: Optional[IKnowledgeMemoryLayer] = None,
        twin_orchestrator: Optional[TwinOrchestrator] = None,
        config: Optional[OrchestrationConfig] = None,
        perception_engine: Optional[IPerceptionEngine] = None,
        writeback_handler: Optional[IMemoryWritebackHandler] = None,
        control_loop: Optional[IControlLoop] = None,
    ) -> None:
        self.reasoning_service = reasoning_service
        self.registry_client = registry_client
        self.agent_adapter = agent_adapter
        self.knowledge_layer = knowledge_layer
        self.twin_orchestrator = twin_orchestrator
        self.config = config or OrchestrationConfig()
        self.perception_engine = perception_engine or StandardPerceptionEngine()
        self.writeback_handler = writeback_handler or StandardMemoryWritebackHandler(knowledge_layer)

        self.control_loop = control_loop or AutonomousControlLoop(
            reasoning_service=self.reasoning_service,
            registry_client=self.registry_client,
            agent_adapter=self.agent_adapter,
            knowledge_layer=self.knowledge_layer,
            twin_orchestrator=self.twin_orchestrator,
            perception_engine=self.perception_engine,
            writeback_handler=self.writeback_handler,
        )

    def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        """
        Execute an autonomous workforce request through the bounded control loop.
        """
        return self.control_loop.run(request, self.config)
