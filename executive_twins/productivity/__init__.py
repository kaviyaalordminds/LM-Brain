"""
Productivity Integration Module.
Provides typed models, provider-independent interfaces, offline dev adapters,
and controlled capability handlers for workspace artifact storage and format export.
"""

from executive_twins.productivity.capability_handlers import (
    ProductivityArtifactExportCapabilityHandler,
    ProductivityArtifactStorageCapabilityHandler,
)
from executive_twins.productivity.dev_adapters import (
    DevTestProductivityAdapter,
    create_productivity_specialist,
)
from executive_twins.productivity.interfaces import (
    IProductivityExporter,
    IProductivityStorageAdapter,
)
from executive_twins.productivity.models import (
    ExportFormat,
    ExportRequest,
    ExportResult,
    StorageProvider,
    StorageRequest,
    StorageResult,
    SyncStatus,
)

__all__ = [
    "DevTestProductivityAdapter",
    "ExportFormat",
    "ExportRequest",
    "ExportResult",
    "IProductivityExporter",
    "IProductivityStorageAdapter",
    "ProductivityArtifactExportCapabilityHandler",
    "ProductivityArtifactStorageCapabilityHandler",
    "StorageProvider",
    "StorageRequest",
    "StorageResult",
    "SyncStatus",
    "create_productivity_specialist",
]
