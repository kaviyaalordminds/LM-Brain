from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    master_orchestrator_port: int = 8000
    planner_url: str = "http://127.0.0.1:8002"
    memory_url: str = "http://127.0.0.1:8001"
    max_concurrent_tasks: int = 5
    default_task_timeout: int = 300
    default_retry_limit: int = 3
    log_level: str = "INFO"
    persistence_backend: str = "memory"

    class Config:
        env_file = ".env"

settings = Settings()
