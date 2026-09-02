class Replanner:
    def __init__(self, planner_client):
        self.planner_client = planner_client

    async def request_recovery_plan(self, execution, failure_context: dict) -> dict:
        original_request = execution.user_request
        return await self.planner_client.create_recovery_plan(original_request, failure_context)
