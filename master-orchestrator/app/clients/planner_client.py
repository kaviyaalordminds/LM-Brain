import httpx

class PlannerUnavailableError(Exception): pass

class PlannerClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8002"):
        self.base_url = base_url

    async def create_plan(self, user_request: str, context: dict, request_id: str) -> dict:
        # In actual implementation, we would make a real request.
        # Handling mocks for testing.
        return {"plan_id": "plan-1", "steps": []}
    
    async def create_recovery_plan(self, original_request: str, current_state: dict) -> dict:
        return {"plan_id": "plan-2", "steps": []}
