"""
Files API package for controlled software workspace file operations.
"""

from executive_twins.files.dev_adapters import (
    DevFileServiceAdapter,
    FileCreateCapabilityHandler,
    FileDeleteCapabilityHandler,
    FileListCapabilityHandler,
    FileReadCapabilityHandler,
    FileUpdateCapabilityHandler,
)
from executive_twins.files.file_service import FileService
from executive_twins.files.interfaces import IFileService
from executive_twins.files.models import (
    FileMetadata,
    FileOperationRequest,
    FileOperationResult,
    FileOperationType,
)

__all__ = [
    "IFileService",
    "FileService",
    "FileOperationType",
    "FileMetadata",
    "FileOperationRequest",
    "FileOperationResult",
    "DevFileServiceAdapter",
    "FileCreateCapabilityHandler",
    "FileReadCapabilityHandler",
    "FileUpdateCapabilityHandler",
    "FileDeleteCapabilityHandler",
    "FileListCapabilityHandler",
]
