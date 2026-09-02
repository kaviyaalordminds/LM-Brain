class SpecialistRegistry:
    def __init__(self):
        self.specialists = {
            "web_development": {"enabled": True, "capabilities": ["frontend", "backend"]},
            "image_generation": {"enabled": True, "capabilities": ["image"]},
            "backend": {"enabled": True, "capabilities": ["backend"]},
            "database": {"enabled": True, "capabilities": ["sql", "nosql"]},
            "api_integration": {"enabled": True, "capabilities": ["api"]},
            "security": {"enabled": True, "capabilities": ["audit"]},
            "testing": {"enabled": True, "capabilities": ["test"]},
            "devops": {"enabled": True, "capabilities": ["deploy"]},
            "ai_ml": {"enabled": True, "capabilities": ["ml"]},
            "research": {"enabled": True, "capabilities": ["search"]}
        }
    
    def get(self, specialist_id: str) -> dict:
        return self.specialists.get(specialist_id)
        
    def is_enabled(self, specialist_id: str) -> bool:
        spec = self.get(specialist_id)
        return spec.get("enabled", False) if spec else False
