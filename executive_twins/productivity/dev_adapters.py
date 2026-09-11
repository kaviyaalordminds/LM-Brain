"""
DEV/TEST Productivity Integration Adapters.
Pure-Python deterministic implementation of artifact storage, export, and format transformation.
All file access passes strictly through sandboxed IFileService.
"""

import csv
import hashlib
import html
import io
import pathlib
import re
from typing import Any, Dict, List, Optional

from executive_twins.files.interfaces import IFileService
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
from executive_twins.schemas.common import SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    RegistryProvenance,
    SpecialistMetadata,
)


def _infer_format_from_path(path: str) -> str:
    """Infer format identifier from file extension."""
    lower = path.lower()
    if lower.endswith(".md") or lower.endswith(".markdown"):
        return "MARKDOWN"
    if lower.endswith(".html") or lower.endswith(".htm"):
        return "HTML"
    if lower.endswith(".csv"):
        return "CSV"
    if lower.endswith(".tsv"):
        return "TSV"
    if lower.endswith(".txt"):
        return "TEXT"
    return "TEXT"


class DevTestProductivityAdapter(IProductivityStorageAdapter, IProductivityExporter):
    """
    DEV_TEST_ONLY_ADAPTER: Offline deterministic adapter for artifact storage and export.
    Simulates provider-independent storage and export boundaries without external network calls.
    """

    def get_provider_status(self, provider: StorageProvider) -> SyncStatus:
        """Query availability status of target storage provider."""
        if provider == StorageProvider.LOCAL:
            return SyncStatus.SUCCESS
        if provider in (StorageProvider.GOOGLE_DRIVE, StorageProvider.ONEDRIVE):
            return SyncStatus.NOT_CONFIGURED
        if provider == StorageProvider.OBSIDIAN:
            return SyncStatus.UNSUPPORTED
        return SyncStatus.UNSUPPORTED

    def can_transform(self, source_format: str, target_format: ExportFormat) -> bool:
        """Check if format transformation is deterministically supported."""
        src = source_format.upper()
        tgt = target_format.value.upper()

        if tgt == "ORIGINAL" or src == tgt:
            return True
        if src in ("MARKDOWN", "TEXT") and tgt == "TEXT":
            return True
        if src in ("MARKDOWN", "TEXT") and tgt == "HTML":
            return True
        if src == "CSV" and tgt == "TSV":
            return True
        if src == "TSV" and tgt == "CSV":
            return True
        return False

    def transform_content(
        self, content: str, source_format: str, target_format: ExportFormat
    ) -> Optional[str]:
        """Apply deterministic transformation from source format to target format."""
        src = source_format.upper()
        tgt = target_format.value.upper()

        if tgt == "ORIGINAL" or src == tgt:
            return content

        # 1. Markdown / Text -> Plain Text
        if src in ("MARKDOWN", "TEXT") and tgt == "TEXT":
            # Strip markdown formatting headers, bold, italics, links
            text = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
            text = re.sub(r"\*([^*]+)\*", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
            return text.strip() + "\n"

        # 2. Markdown / Text -> HTML
        if src in ("MARKDOWN", "TEXT") and tgt == "HTML":
            lines = content.splitlines()
            body_parts: List[str] = []
            for line in lines:
                if line.startswith("# "):
                    body_parts.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
                elif line.startswith("## "):
                    body_parts.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
                elif line.startswith("### "):
                    body_parts.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
                elif line.startswith("> "):
                    body_parts.append(f"<blockquote>{html.escape(line[2:].strip())}</blockquote>")
                elif line.startswith("- ") or line.startswith("* "):
                    body_parts.append(f"<li>{html.escape(line[2:].strip())}</li>")
                elif line.strip():
                    body_parts.append(f"<p>{html.escape(line.strip())}</p>")

            inner_html = "\n    ".join(body_parts)
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Exported Artifact</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; padding: 2rem; color: #1e293b; background: #ffffff; }}
    blockquote {{ border-left: 4px solid #94a3b8; padding-left: 1rem; color: #64748b; margin: 1rem 0; }}
  </style>
</head>
<body>
    {inner_html}
</body>
</html>
"""

        # 3. CSV -> TSV
        if src == "CSV" and tgt == "TSV":
            try:
                reader = csv.reader(io.StringIO(content))
                out = io.StringIO()
                writer = csv.writer(out, delimiter="\t", lineterminator="\n")
                for row in reader:
                    writer.writerow(row)
                return out.getvalue()
            except Exception:
                return None

        # 4. TSV -> CSV
        if src == "TSV" and tgt == "CSV":
            try:
                reader = csv.reader(io.StringIO(content), delimiter="\t")
                out = io.StringIO()
                writer = csv.writer(out, delimiter=",", lineterminator="\n")
                for row in reader:
                    writer.writerow(row)
                return out.getvalue()
            except Exception:
                return None

        return None

    def store_artifact(
        self, request: StorageRequest, file_service: IFileService
    ) -> StorageResult:
        """Store an artifact into target logical destination within workspace."""
        provider_status = self.get_provider_status(request.provider)
        src_art = f"workspace://{request.source_workspace}/{request.source_relative_path}"

        if provider_status != SyncStatus.SUCCESS:
            return StorageResult(
                status=provider_status,
                source_artifact=src_art,
                provider=request.provider,
                error_message=f"Storage provider '{request.provider.value}' is not configured/supported in offline environment.",
            )

        read_res = file_service.read_file(request.source_relative_path)
        if not read_res.success or read_res.content is None:
            return StorageResult(
                status=SyncStatus.FAILED,
                source_artifact=src_art,
                provider=request.provider,
                error_message=read_res.error_message or f"Failed to read source artifact '{request.source_relative_path}'.",
            )

        dest_rel = request.destination_relative_path or f"storage/{request.source_relative_path}"
        dest_ws = request.destination_workspace or request.source_workspace
        dest_art = f"workspace://{dest_ws}/{dest_rel}"

        write_res = file_service.create_file(dest_rel, read_res.content, overwrite=request.overwrite)
        if not write_res.success:
            return StorageResult(
                status=SyncStatus.FAILED,
                source_artifact=src_art,
                destination_artifact=dest_art,
                provider=request.provider,
                error_message=write_res.error_message or f"Failed to write destination artifact '{dest_rel}'.",
            )

        checksum = hashlib.sha256(read_res.content.encode("utf-8")).hexdigest()
        return StorageResult(
            status=SyncStatus.SUCCESS,
            source_artifact=src_art,
            destination_artifact=dest_art,
            provider=request.provider,
            checksum_sha256=checksum,
            details={"size_bytes": len(read_res.content)},
        )

    def retrieve_artifact(
        self, relative_path: str, file_service: IFileService
    ) -> Optional[str]:
        """Retrieve stored artifact content from workspace file service."""
        read_res = file_service.read_file(relative_path)
        if read_res.success:
            return read_res.content
        return None

    def export_artifact(
        self, request: ExportRequest, file_service: IFileService
    ) -> ExportResult:
        """Export and format-transform an artifact into destination path."""
        provider_status = self.get_provider_status(request.provider)
        src_art = f"workspace://{request.source_workspace}/{request.source_relative_path}"

        if provider_status != SyncStatus.SUCCESS:
            return ExportResult(
                status=provider_status,
                source_artifact=src_art,
                provider=request.provider,
                format=request.requested_format,
                error_message=f"Storage provider '{request.provider.value}' is not configured/supported for export.",
            )

        read_res = file_service.read_file(request.source_relative_path)
        if not read_res.success or read_res.content is None:
            return ExportResult(
                status=SyncStatus.FAILED,
                source_artifact=src_art,
                provider=request.provider,
                format=request.requested_format,
                error_message=read_res.error_message or f"Failed to read source artifact '{request.source_relative_path}'.",
            )

        source_format = _infer_format_from_path(request.source_relative_path)
        transformed = self.transform_content(read_res.content, source_format, request.requested_format)

        if transformed is None:
            return ExportResult(
                status=SyncStatus.UNSUPPORTED,
                source_artifact=src_art,
                provider=request.provider,
                format=request.requested_format,
                error_message=f"Transformation from format '{source_format}' to '{request.requested_format.value}' is unsupported.",
            )

        # Compute destination path if not provided
        if request.destination_relative_path:
            dest_rel = request.destination_relative_path
        else:
            stem = pathlib.Path(request.source_relative_path).stem
            if request.requested_format == ExportFormat.MARKDOWN:
                ext = "md"
            elif request.requested_format == ExportFormat.HTML:
                ext = "html"
            elif request.requested_format == ExportFormat.CSV:
                ext = "csv"
            elif request.requested_format == ExportFormat.TSV:
                ext = "tsv"
            elif request.requested_format == ExportFormat.TEXT:
                ext = "txt"
            else:
                ext = pathlib.Path(request.source_relative_path).suffix.lstrip(".") or "txt"
            dest_rel = f"exports/{stem}.{ext}"

        dest_ws = request.destination_workspace or request.source_workspace
        dest_art = f"workspace://{dest_ws}/{dest_rel}"

        write_res = file_service.create_file(dest_rel, transformed, overwrite=request.overwrite)
        if not write_res.success:
            return ExportResult(
                status=SyncStatus.FAILED,
                source_artifact=src_art,
                destination_artifact=dest_art,
                provider=request.provider,
                format=request.requested_format,
                error_message=write_res.error_message or f"Failed to write exported artifact '{dest_rel}'.",
            )

        checksum = hashlib.sha256(transformed.encode("utf-8")).hexdigest()
        return ExportResult(
            status=SyncStatus.SUCCESS,
            source_artifact=src_art,
            destination_artifact=dest_art,
            provider=request.provider,
            format=request.requested_format,
            checksum_sha256=checksum,
            details={"size_bytes": len(transformed)},
        )


def create_productivity_specialist(
    specialist_id: str = "spec_productivity_01",
    name: str = "Productivity Integration",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for Productivity Integration.
    Declares artifact_export and productivity_storage capabilities into the registry.
    """
    capabilities = [
        Capability(
            name="artifact_export",
            description="Controlled export, format conversion, and target preparation of workspace artifacts",
            required_tools=["file_service"],
        ),
        Capability(
            name="productivity_storage",
            description="Controlled artifact movement, backup, and storage target management",
            required_tools=["file_service"],
        ),
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=["file_service", "productivity_storage"],
        security_level=security_level,
        provenance=RegistryProvenance(
            registry_id="local_dev_registry",
            snapshot_id="snap_productivity_v1",
        ),
    )
