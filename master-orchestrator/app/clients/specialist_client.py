class SpecialistUnavailableError(Exception): pass
class SpecialistDispatchError(Exception): pass

class SpecialistClient:
    async def dispatch(self, task_request: dict) -> dict:
        return {
            "result_id": "res-1",
            "task_id": task_request.get("task_id"),
            "status": "SUCCESS",
            "output": "mock",
            "artifacts": [],
            "verification": {"verdict": True, "checks": [], "reason": "", "errors": []}
        }
        
    async def check_health(self, specialist_id: str) -> bool:
        return True
