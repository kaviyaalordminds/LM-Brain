from typing import List

class OrchestratorPermissions:
    @staticmethod
    def validate_permissions(permissions: List[str]) -> bool:
        return "ADMIN" not in permissions
