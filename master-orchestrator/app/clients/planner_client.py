import httpx
from typing import Any, Dict

class PlannerUnavailableError(Exception): pass
class PlannerContractViolationError(Exception): pass

class PlannerClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8002", timeout_seconds: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def create_plan(self, user_request: str, context: dict, request_id: str) -> dict:
        url = f"{self.base_url}/api/v1/plans"
        payload = {
            "user_request": user_request,
            "request_id": request_id,
            "context": context or {}
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 500:
                    raise PlannerUnavailableError(f"Planner service error {resp.status_code}: {resp.text}")
                if resp.status_code not in (200, 201):
                    raise PlannerContractViolationError(f"Planner returned unexpected status {resp.status_code}: {resp.text}")
                plan_data = resp.json()

                if not isinstance(plan_data, dict) or ("steps" not in plan_data and "steps" not in plan_data.get("plan", {})):
                    raise PlannerContractViolationError("Planner response missing steps structure")
                return plan_data
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise PlannerUnavailableError(f"Planner unavailable at {url}: {str(e)}") from e
        except (PlannerUnavailableError, PlannerContractViolationError):
            raise
        except Exception as e:
            raise PlannerUnavailableError(f"Unexpected error communicating with Planner: {str(e)}") from e

    async def create_recovery_plan(self, original_request: str, failure_context: dict) -> dict:
        url = f"{self.base_url}/api/v1/plans"
        recovery_prompt = (
            f"RECOVERY PLAN REQUIRED.\n"
            f"Original Goal: {original_request}\n"
            f"Failure Context: {failure_context}\n"
            f"Please generate an adaptive recovery plan addressing the failure while keeping completed work reusable."
        )
        payload = {
            "user_request": recovery_prompt,
            "context": {"failure_context": failure_context, "is_recovery": True}
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise PlannerUnavailableError(f"Planner recovery plan request failed: {resp.status_code} {resp.text}")
                return resp.json()
        except Exception as e:
            raise PlannerUnavailableError(f"Failed to obtain recovery plan from Planner: {str(e)}") from e

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/v1/health")
                return resp.status_code == 200
        except Exception:
            return False

