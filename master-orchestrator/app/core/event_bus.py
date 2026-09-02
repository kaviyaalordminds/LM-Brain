from typing import Callable, Dict
from app.models.events import ExecutionEvent

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, Dict[str, Callable]] = {}

    def publish(self, event: ExecutionEvent) -> None:
        subs = self.subscribers.get(event.execution_id, {})
        for cb in subs.values():
            cb(event)

    def subscribe(self, execution_id: str, callback: Callable) -> str:
        if execution_id not in self.subscribers:
            self.subscribers[execution_id] = {}
        sub_id = f"sub_{len(self.subscribers[execution_id])}"
        self.subscribers[execution_id][sub_id] = callback
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        for execution_id, subs in self.subscribers.items():
            if subscription_id in subs:
                del subs[subscription_id]
