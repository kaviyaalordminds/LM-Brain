from abc import ABC, abstractmethod
from typing import List, Optional

class ExecutionRepository(ABC):
    @abstractmethod
    def save_execution(self, execution): pass
    @abstractmethod
    def get_execution(self, execution_id: str): pass
    @abstractmethod
    def update_execution(self, execution): pass
    @abstractmethod
    def list_executions(self): pass
    @abstractmethod
    def save_attempt(self, attempt): pass
    @abstractmethod
    def get_attempts(self, execution_id: str): pass
    @abstractmethod
    def save_artifact(self, artifact): pass
    @abstractmethod
    def get_artifacts(self, execution_id: str): pass
    @abstractmethod
    def save_plan_version(self, plan): pass
    @abstractmethod
    def get_plan_versions(self, plan_id: str): pass

class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self):
        self.executions = {}
        self.attempts = []
        self.artifacts = []
        self.plans = []
    
    def save_execution(self, execution):
        self.executions[execution.execution_id] = execution
        
    def get_execution(self, execution_id: str):
        return self.executions.get(execution_id)
        
    def update_execution(self, execution):
        self.executions[execution.execution_id] = execution
        
    def list_executions(self):
        return list(self.executions.values())
        
    def save_attempt(self, attempt):
        self.attempts.append(attempt)
        
    def get_attempts(self, execution_id: str):
        return [a for a in self.attempts if a.execution_id == execution_id]
        
    def save_artifact(self, artifact):
        self.artifacts.append(artifact)
        
    def get_artifacts(self, execution_id: str):
        return [a for a in self.artifacts if a.execution_id == execution_id]
        
    def save_plan_version(self, plan):
        self.plans.append(plan)
        
    def get_plan_versions(self, plan_id: str):
        return [p for p in self.plans if p.get("plan_id") == plan_id]
