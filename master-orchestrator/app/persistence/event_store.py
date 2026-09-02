from abc import ABC, abstractmethod
from typing import List

class EventStore(ABC):
    @abstractmethod
    def append(self, event): pass
    
    @abstractmethod
    def get_events(self, execution_id: str): pass
    
    @abstractmethod
    def get_events_by_type(self, execution_id: str, event_type: str): pass

class InMemoryEventStore(EventStore):
    def __init__(self):
        self.events = []
        
    def append(self, event):
        self.events.append(event)
        
    def get_events(self, execution_id: str):
        return [e for e in self.events if e.execution_id == execution_id]
        
    def get_events_by_type(self, execution_id: str, event_type: str):
        return [e for e in self.events if e.execution_id == execution_id and e.event_type == event_type]
