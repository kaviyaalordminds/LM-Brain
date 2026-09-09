"""
Interfaces and abstract protocols for Controlled Docker Execution Layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from executive_twins.docker.models import DockerResult
from executive_twins.workspace.interfaces import ISoftwareWorkspace


class IDockerService(ABC):
    """
    Controlled Docker Service Interface.
    Provides safe, bounded, and structured container operations within an ISoftwareWorkspace boundary.
    Specialists must NEVER receive arbitrary CLI access, shell access, host filesystem access,
    Docker socket access, or privileged container capabilities.
    """

    @property
    @abstractmethod
    def workspace(self) -> Optional[ISoftwareWorkspace]:
        """Return the underlying controlled workspace security boundary, if associated."""
        pass

    @abstractmethod
    def check_availability(self) -> DockerResult:
        """Verify whether the Docker CLI and Docker daemon are available and operational."""
        pass

    @abstractmethod
    def build_image(
        self,
        image_name: str,
        dockerfile_path: str = "Dockerfile",
        build_context: str = ".",
        timeout_seconds: Optional[float] = None,
    ) -> DockerResult:
        """
        Build a Docker image strictly from the workspace-contained build context and Dockerfile.
        Arbitrary host paths, registry pushes, and dangerous build arguments are forbidden.
        """
        pass

    @abstractmethod
    def run_container(
        self,
        image_name: str,
        container_name: Optional[str] = None,
        command: Optional[List[str]] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        memory_limit: Optional[str] = None,
        cpu_limit: Optional[float] = None,
    ) -> DockerResult:
        """
        Run a bounded, unprivileged container from an authorized image.
        Host filesystem mounts, host networking, host namespaces, and privileged modes are strictly forbidden.
        """
        pass

    @abstractmethod
    def stop_container(
        self,
        container_name: str,
        timeout_seconds: Optional[float] = 10.0,
    ) -> DockerResult:
        """Stop an active container created by the controlled service."""
        pass

    @abstractmethod
    def remove_container(
        self,
        container_name: str,
        force: bool = False,
    ) -> DockerResult:
        """Remove a container created by the controlled service."""
        pass

    @abstractmethod
    def inspect_container(
        self,
        container_name: str,
    ) -> DockerResult:
        """Retrieve structured status and state inspection for a container."""
        pass
