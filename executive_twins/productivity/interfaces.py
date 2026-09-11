"""
Productivity Integration Abstract Interfaces.
Provides provider-independent contracts for artifact storage and format export.
"""

from abc import ABC, abstractmethod
from typing import Optional

from executive_twins.files.interfaces import IFileService
from executive_twins.productivity.models import (
    ExportFormat,
    ExportRequest,
    ExportResult,
    StorageProvider,
    StorageRequest,
    StorageResult,
    SyncStatus,
)


class IProductivityStorageAdapter(ABC):
    """
    Authoritative abstraction for storing and organizing workspace artifacts
    across logical storage providers.
    """

    @abstractmethod
    def store_artifact(
        self, request: StorageRequest, file_service: IFileService
    ) -> StorageResult:
        """Store an artifact into a logical destination using sandboxed file service."""
        pass

    @abstractmethod
    def retrieve_artifact(
        self, relative_path: str, file_service: IFileService
    ) -> Optional[str]:
        """Retrieve stored artifact content from workspace file service."""
        pass

    @abstractmethod
    def get_provider_status(self, provider: StorageProvider) -> SyncStatus:
        """Query availability and configuration status for a given storage provider."""
        pass


class IProductivityExporter(ABC):
    """
    Authoritative abstraction for exporting workspace artifacts and applying
    deterministic format representations.
    """

    @abstractmethod
    def export_artifact(
        self, request: ExportRequest, file_service: IFileService
    ) -> ExportResult:
        """Export an artifact to target destination and format."""
        pass

    @abstractmethod
    def can_transform(
        self, source_format: str, target_format: ExportFormat
    ) -> bool:
        """Check if a deterministic format transformation is supported."""
        pass

    @abstractmethod
    def transform_content(
        self, content: str, source_format: str, target_format: ExportFormat
    ) -> Optional[str]:
        """Apply deterministic transformation from source to target format."""
        pass
