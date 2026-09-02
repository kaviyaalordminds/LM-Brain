import httpx
from typing import Any, Dict, Optional

class MemoryUnavailableError(Exception): pass

class MemoryClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8001", timeout_seconds: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, task_id: str, context: dict = None, filters: dict = None) -> dict:
        url = f"{self.base_url}/api/v1/memory/search"
        payload = {
            "query": query,
            "task_id": task_id,
            "context": context or {},
            "filters": filters
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise MemoryUnavailableError(f"Memory search returned {resp.status_code}: {resp.text}")
                return resp.json()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise MemoryUnavailableError(f"Memory service unavailable at {url}: {str(e)}") from e
        except MemoryUnavailableError:
            raise
        except Exception as e:
            raise MemoryUnavailableError(f"Error querying Memory search: {str(e)}") from e

    async def research(self, query: str, task_id: str) -> dict:
        url = f"{self.base_url}/api/v1/memory/research"
        payload = {
            "query": query,
            "task_id": task_id
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise MemoryUnavailableError(f"Memory research returned {resp.status_code}: {resp.text}")
                return resp.json()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise MemoryUnavailableError(f"Memory research service unavailable at {url}: {str(e)}") from e
        except MemoryUnavailableError:
            raise
        except Exception as e:
            raise MemoryUnavailableError(f"Error querying Memory research: {str(e)}") from e

    async def get_context(self, task_id: str) -> dict:
        url = f"{self.base_url}/api/v1/memory/context/{task_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return {}
                if resp.status_code != 200:
                    raise MemoryUnavailableError(f"Memory get_context returned {resp.status_code}: {resp.text}")
                return resp.json()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise MemoryUnavailableError(f"Memory service unavailable at {url}: {str(e)}") from e
        except MemoryUnavailableError:
            raise
        except Exception as e:
            raise MemoryUnavailableError(f"Error retrieving context from Memory: {str(e)}") from e

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

