class MemoryUnavailableError(Exception): pass

class MemoryClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url

    async def search(self, query: str, task_id: str, context: dict = None, filters: dict = None) -> dict:
        return {}
        
    async def research(self, query: str, task_id: str) -> dict:
        return {}
        
    async def get_context(self, task_id: str) -> dict:
        return {}
