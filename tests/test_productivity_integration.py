"""
Unit tests for Productivity Integration Foundation & Specialist (Member 2).
Verifies StorageProvider, ExportFormat, ExportRequest/Result, DevTestProductivityAdapter,
transformations (MD->Text, MD->HTML, CSV<->TSV, unsupported), security path validation,
capability handlers, registry discovery, and SpecialistExecutionEngine integration.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.productivity import (
    DevTestProductivityAdapter,
    ExportFormat,
    ExportRequest,
    ExportResult,
    IProductivityExporter,
    IProductivityStorageAdapter,
    ProductivityArtifactExportCapabilityHandler,
    ProductivityArtifactStorageCapabilityHandler,
    StorageProvider,
    StorageRequest,
    StorageResult,
    SyncStatus,
    create_productivity_specialist,
)
from executive_twins.schemas.common import SecurityContext, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


def make_delegation_request(
    delegation_id: str,
    capability_name: str,
    inputs: dict,
    specialist_id: str = "spec_productivity_01",
    task: str = "Productivity task",
    objective: str = "Execute productivity operation",
    expected_output: str = "Exported/stored artifact output",
) -> DelegationRequest:
    """Helper creating a fully populated DelegationRequest."""
    return DelegationRequest(
        delegation_id=delegation_id,
        parent_task_id=f"parent_{delegation_id}",
        executive_twin_id="twin_cmo",
        specialist_id=specialist_id,
        objective=objective,
        task=task,
        required_capabilities=[capability_name],
        inputs=inputs,
        expected_output=expected_output,
    )


# ==============================================================================
# 1. Models and Enums Tests
# ==============================================================================


class TestProductivityModels:
    def test_enums(self):
        # StorageProvider
        assert StorageProvider.LOCAL.value == "LOCAL"
        assert StorageProvider.GOOGLE_DRIVE.value == "GOOGLE_DRIVE"
        assert StorageProvider.ONEDRIVE.value == "ONEDRIVE"
        assert StorageProvider.OBSIDIAN.value == "OBSIDIAN"

        # ExportFormat
        assert ExportFormat.ORIGINAL.value == "ORIGINAL"
        assert ExportFormat.MARKDOWN.value == "MARKDOWN"
        assert ExportFormat.HTML.value == "HTML"
        assert ExportFormat.CSV.value == "CSV"
        assert ExportFormat.TSV.value == "TSV"
        assert ExportFormat.TEXT.value == "TEXT"

        # SyncStatus
        assert SyncStatus.NOT_STARTED.value == "NOT_STARTED"
        assert SyncStatus.SUCCESS.value == "SUCCESS"
        assert SyncStatus.FAILED.value == "FAILED"
        assert SyncStatus.UNSUPPORTED.value == "UNSUPPORTED"
        assert SyncStatus.NOT_CONFIGURED.value == "NOT_CONFIGURED"

    def test_export_request_validation_valid(self):
        req = ExportRequest(
            source_workspace="ws_1",
            source_relative_path="docs/report.md",
            destination_relative_path="exports/report.html",
            provider=StorageProvider.LOCAL,
            requested_format=ExportFormat.HTML,
        )
        assert req.source_relative_path == "docs/report.md"
        assert req.destination_relative_path == "exports/report.html"
        assert req.provider == StorageProvider.LOCAL
        assert req.requested_format == ExportFormat.HTML

    def test_export_request_rejection_path_traversal(self):
        with pytest.raises(ValidationError):
            ExportRequest(
                source_relative_path="../outside/secret.txt",
            )
        with pytest.raises(ValidationError):
            ExportRequest(
                source_relative_path="docs/../../etc/passwd",
            )

    def test_export_request_rejection_absolute_path(self):
        with pytest.raises(ValidationError):
            ExportRequest(
                source_relative_path="/root/system.log",
            )
        with pytest.raises(ValidationError):
            ExportRequest(
                source_relative_path="C:/Windows/system32/cmd.exe",
            )

    def test_storage_request_and_result(self):
        req = StorageRequest(
            source_workspace="ws_1",
            source_relative_path="reports/q3.csv",
            destination_relative_path="backup/q3.csv",
            provider=StorageProvider.LOCAL,
        )
        assert req.source_relative_path == "reports/q3.csv"

        res = StorageResult(
            status=SyncStatus.SUCCESS,
            source_artifact="workspace://ws_1/reports/q3.csv",
            destination_artifact="workspace://ws_1/backup/q3.csv",
            provider=StorageProvider.LOCAL,
            checksum_sha256="abc123hash",
        )
        assert res.status == SyncStatus.SUCCESS
        assert res.checksum_sha256 == "abc123hash"


# ==============================================================================
# 2. Adapter and Format Transformations Tests
# ==============================================================================


class TestProductivityAdapterAndTransformations:
    @pytest.fixture
    def workspace_setup(self):
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("default")
        return ws_adapter, file_adapter

    def test_provider_status_reporting(self):
        adapter = DevTestProductivityAdapter()
        assert adapter.get_provider_status(StorageProvider.LOCAL) == SyncStatus.SUCCESS
        assert adapter.get_provider_status(StorageProvider.GOOGLE_DRIVE) == SyncStatus.NOT_CONFIGURED
        assert adapter.get_provider_status(StorageProvider.ONEDRIVE) == SyncStatus.NOT_CONFIGURED
        assert adapter.get_provider_status(StorageProvider.OBSIDIAN) == SyncStatus.UNSUPPORTED

    def test_markdown_to_text_transformation(self):
        adapter = DevTestProductivityAdapter()
        md_content = "# Executive Summary\n\n**Goal**: Deploy *autonomous* workforce.\n\n> Important note\n\n- Point 1\n- Point 2"
        text = adapter.transform_content(md_content, "MARKDOWN", ExportFormat.TEXT)
        assert text is not None
        assert "#" not in text
        assert "**" not in text
        assert "Executive Summary" in text
        assert "Goal: Deploy autonomous workforce." in text

    def test_markdown_to_html_transformation(self):
        adapter = DevTestProductivityAdapter()
        md_content = "# Title Heading\n\n## Subheading\n\nParagraph text.\n\n> Blockquote text"
        html_out = adapter.transform_content(md_content, "MARKDOWN", ExportFormat.HTML)
        assert html_out is not None
        assert "<!DOCTYPE html>" in html_out
        assert "<h1>Title Heading</h1>" in html_out
        assert "<h2>Subheading</h2>" in html_out
        assert "<p>Paragraph text.</p>" in html_out
        assert "<blockquote>Blockquote text</blockquote>" in html_out

    def test_csv_to_tsv_transformation(self):
        adapter = DevTestProductivityAdapter()
        csv_content = 'Name,Role,Salary\nAlice,"Staff Eng",150000\nBob,"Manager",160000\n'
        tsv_out = adapter.transform_content(csv_content, "CSV", ExportFormat.TSV)
        assert tsv_out is not None
        assert "Name\tRole\tSalary" in tsv_out
        assert "Alice\tStaff Eng\t150000" in tsv_out

    def test_tsv_to_csv_transformation(self):
        adapter = DevTestProductivityAdapter()
        tsv_content = "Item\tCount\tPrice\nWidget\t10\t5.50\n"
        csv_out = adapter.transform_content(tsv_content, "TSV", ExportFormat.CSV)
        assert csv_out is not None
        assert "Item,Count,Price" in csv_out
        assert "Widget,10,5.50" in csv_out

    def test_unsupported_transformation(self):
        adapter = DevTestProductivityAdapter()
        # HTML to CSV is unsupported
        res = adapter.transform_content("<html><body>data</body></html>", "HTML", ExportFormat.CSV)
        assert res is None
        assert adapter.can_transform("HTML", ExportFormat.CSV) is False

    def test_local_artifact_storage(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("source/data.txt", "Essential content payload.")

        adapter = DevTestProductivityAdapter()
        req = StorageRequest(
            source_workspace="default",
            source_relative_path="source/data.txt",
            destination_relative_path="archive/data.txt",
            provider=StorageProvider.LOCAL,
        )

        res = adapter.store_artifact(req, fs)
        assert res.status == SyncStatus.SUCCESS
        assert res.destination_artifact == "workspace://default/archive/data.txt"
        assert res.checksum_sha256 is not None

        retrieved = adapter.retrieve_artifact("archive/data.txt", fs)
        assert retrieved == "Essential content payload."

    def test_unconfigured_provider_storage_rejection(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("doc.md", "# Heading")

        adapter = DevTestProductivityAdapter()
        req = StorageRequest(
            source_workspace="default",
            source_relative_path="doc.md",
            provider=StorageProvider.GOOGLE_DRIVE,
        )

        res = adapter.store_artifact(req, fs)
        assert res.status == SyncStatus.NOT_CONFIGURED
        assert "not configured" in res.error_message.lower()


# ==============================================================================
# 3. Capability Handlers Unit Tests
# ==============================================================================


class TestProductivityCapabilityHandlers:
    @pytest.fixture
    def workspace_setup(self):
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("default")
        return ws_adapter, file_adapter

    def test_export_handler_markdown_to_html(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("reports/summary.md", "# Q3 Autonomous Report\n\nAll tasks completed.\n")

        handler = ProductivityArtifactExportCapabilityHandler(file_adapter=file_adapter)
        specialist = create_productivity_specialist()

        req = make_delegation_request(
            delegation_id="del_exp_01",
            capability_name="artifact_export",
            inputs={
                "source_relative_path": "reports/summary.md",
                "destination_relative_path": "exports/summary.html",
                "requested_format": "HTML",
                "workspace_id": "default",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.artifacts) == 1
        assert out.artifacts[0] == "workspace://default/exports/summary.html"
        assert len(out.additional_evidence) == 2

        art_ev = next(e for e in out.additional_evidence if isinstance(e, ArtifactEvidence))
        assert art_ev.mime_type == "text/html"
        assert art_ev.checksum_sha256 is not None

        verif_ev = next(e for e in out.additional_evidence if isinstance(e, VerificationEvidence))
        assert verif_ev.verified_status == "VERIFIED"

        read_res = fs.read_file("exports/summary.html")
        assert read_res.success is True
        assert "<!DOCTYPE html>" in read_res.content
        assert "<h1>Q3 Autonomous Report</h1>" in read_res.content

    def test_storage_handler_placement(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("raw/sample.csv", "A,B,C\n1,2,3\n")

        handler = ProductivityArtifactStorageCapabilityHandler(file_adapter=file_adapter)
        specialist = create_productivity_specialist()

        req = make_delegation_request(
            delegation_id="del_store_01",
            capability_name="productivity_storage",
            inputs={
                "source_relative_path": "raw/sample.csv",
                "destination_relative_path": "vault/sample.csv",
                "workspace_id": "default",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.artifacts) == 1
        assert out.artifacts[0] == "workspace://default/vault/sample.csv"

        read_res = fs.read_file("vault/sample.csv")
        assert read_res.success is True
        assert "A,B,C\n1,2,3\n" in read_res.content

    def test_export_handler_unsupported_format(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("raw/page.html", "<html><body>test</body></html>")

        handler = ProductivityArtifactExportCapabilityHandler(file_adapter=file_adapter)
        specialist = create_productivity_specialist()

        req = make_delegation_request(
            delegation_id="del_exp_fail_01",
            capability_name="artifact_export",
            inputs={
                "source_relative_path": "raw/page.html",
                "requested_format": "CSV",
                "workspace_id": "default",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is False
        assert "EXPORT_FAILED" in out.output_text
        assert any("unsupported" in err.lower() for err in out.errors)

    def test_handler_path_traversal_rejection(self, workspace_setup):
        _, file_adapter = workspace_setup
        handler = ProductivityArtifactExportCapabilityHandler(file_adapter=file_adapter)

        err = handler.validate_parameters({
            "source_relative_path": "../../secret.env",
            "workspace_id": "default",
        })
        assert err is not None
        assert "traversal" in err.lower()


# ==============================================================================
# 4. Specialist Registry & Execution Engine Integration
# ==============================================================================


class TestProductivityExecutionEngineIntegration:
    @pytest.fixture
    def engine_setup(self):
        registry = InMemorySpecialistRegistryAdapter()
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("default")

        spec = create_productivity_specialist()
        registry.register_specialist(spec)

        engine = SpecialistExecutionEngine(
            registry_client=registry,
        )

        engine.register_handler(ProductivityArtifactExportCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(ProductivityArtifactStorageCapabilityHandler(file_adapter=file_adapter))

        return engine, file_adapter, registry

    def test_registry_registration_and_discovery(self, engine_setup):
        _, _, registry = engine_setup
        spec = registry.get_specialist_by_id("spec_productivity_01")
        assert spec is not None
        assert spec.name == "Productivity Integration"
        assert spec.status == SpecialistStatus.ACTIVE
        assert "file_service" in spec.authorized_tools
        assert "productivity_storage" in spec.authorized_tools

        sec_ctx = SecurityContext(actor_id="test_actor", session_id="test_session")
        reqs = [CapabilityRequirement(capability_name="artifact_export", description="Export artifact")]
        matching = registry.discover_specialists(reqs, sec_ctx)
        assert len(matching) == 1
        assert matching[0].selected_specialist.specialist_id == "spec_productivity_01"

        reqs_store = [CapabilityRequirement(capability_name="productivity_storage", description="Store artifact")]
        matching_store = registry.discover_specialists(reqs_store, sec_ctx)
        assert len(matching_store) == 1
        assert matching_store[0].selected_specialist.specialist_id == "spec_productivity_01"

    def test_engine_artifact_export_e2e(self, engine_setup):
        engine, file_adapter, _ = engine_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("docs/guide.md", "# Autonomous Workforce\n\nDeterministic execution.\n")

        req = make_delegation_request(
            delegation_id="del_e2e_prod_exp_01",
            capability_name="artifact_export",
            inputs={
                "source_relative_path": "docs/guide.md",
                "destination_relative_path": "dist/guide.txt",
                "requested_format": "TEXT",
                "workspace_id": "default",
            },
        )

        result: DelegationResult = engine.execute_delegation(req)

        assert result.status == "SUCCESS"
        assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)
        assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)
        assert len(result.artifacts) == 1

        file_res = fs.read_file("dist/guide.txt")
        assert file_res.success is True
        assert "#" not in file_res.content
        assert "Autonomous Workforce" in file_res.content

    def test_engine_productivity_storage_e2e(self, engine_setup):
        engine, file_adapter, _ = engine_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("artifacts/sheet.csv", "ID,Name\n1,Alice\n")

        req = make_delegation_request(
            delegation_id="del_e2e_prod_store_01",
            capability_name="productivity_storage",
            inputs={
                "source_relative_path": "artifacts/sheet.csv",
                "destination_relative_path": "backups/sheet.csv",
                "workspace_id": "default",
            },
        )

        result: DelegationResult = engine.execute_delegation(req)

        assert result.status == "SUCCESS"
        assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)
        assert len(result.artifacts) == 1

        file_res = fs.read_file("backups/sheet.csv")
        assert file_res.success is True
        assert "1,Alice" in file_res.content

    def test_engine_unauthorized_capability_rejection(self, engine_setup):
        engine, _, _ = engine_setup

        req = make_delegation_request(
            delegation_id="del_unauth_prod_01",
            capability_name="unauthorized_cloud_upload",
            inputs={"source_relative_path": "docs/guide.md"},
        )

        result: DelegationResult = engine.execute_delegation(req)
        assert result.status == "FAILED" or result.status.value == "FAILED"
        assert len(result.errors) > 0

    def test_deterministic_repeated_execution(self, engine_setup):
        engine, file_adapter, _ = engine_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("test/table.csv", "Col1,Col2\nVal1,Val2\n")

        for idx in range(3):
            req = make_delegation_request(
                delegation_id=f"del_repeat_{idx}",
                capability_name="artifact_export",
                inputs={
                    "source_relative_path": "test/table.csv",
                    "destination_relative_path": "exports/table.tsv",
                    "requested_format": "TSV",
                    "workspace_id": "default",
                },
            )
            result = engine.execute_delegation(req)
            assert result.status == "SUCCESS"

        file_res = fs.read_file("exports/table.tsv")
        assert file_res.success is True
        assert "Col1\tCol2\nVal1\tVal2\n" == file_res.content
