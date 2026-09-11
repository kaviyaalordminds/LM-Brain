"""
Unit tests for Spreadsheet Foundation & Specialist (Member 2 Day 2 Item 5).
Verifies Spreadsheet models, builders, renderers, parsers, templates, capability handlers,
specialist metadata, FileService persistence, and SpecialistExecutionEngine integration.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import pytest
from pydantic import ValidationError

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.schemas.common import FactState, SecurityContext, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.spreadsheets import (
    CSVSpreadsheetParser,
    CSVSpreadsheetRenderer,
    CellType,
    ColumnSpec,
    DevTestSpreadsheetAdapter,
    ISpreadsheetBuilder,
    ISpreadsheetParser,
    ISpreadsheetRenderer,
    ISpreadsheetSpecialist,
    SpreadsheetBuilder,
    SpreadsheetCell,
    SpreadsheetEditingCapabilityHandler,
    SpreadsheetFormat,
    SpreadsheetGenerationCapabilityHandler,
    SpreadsheetMetadata,
    SpreadsheetTemplate,
    SpreadsheetValidationCapabilityHandler,
    Workbook,
    Worksheet,
    create_spreadsheet_specialist,
)
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


def make_delegation_request(
    delegation_id: str,
    capability_name: str,
    inputs: dict,
    specialist_id: str = "spec_spreadsheet_01",
    task: str = "Spreadsheet task",
    objective: str = "Execute spreadsheet operation",
    expected_output: str = "Spreadsheet output",
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


class DummySpreadsheetSpecialist(ISpreadsheetSpecialist):
    """Test concrete implementation of ISpreadsheetSpecialist interface."""

    def synthesize_spreadsheet(
        self,
        title: str,
        topic: str,
        columns: Optional[List[str]] = None,
        rows: Optional[List[List[Any]]] = None,
    ) -> Workbook:
        builder = SpreadsheetBuilder(title=title)
        if columns:
            builder.add_row(columns)
        if rows:
            for r in rows:
                builder.add_row(r)
        return builder.build()

    def edit_spreadsheet(
        self,
        workbook: Workbook,
        instructions: str,
        edits: Dict[str, Any],
    ) -> Workbook:
        if "set_cell" in edits:
            cell_data = edits["set_cell"]
            workbook.active_sheet.set_cell(
                row=cell_data["row"],
                column=cell_data["column"],
                value=cell_data["value"],
            )
        return workbook

    def validate_spreadsheet(
        self,
        workbook: Workbook,
    ) -> Dict[str, Any]:
        return {
            "valid": len(workbook.title) > 0 and len(workbook.worksheets) > 0,
            "total_rows": sum(s.row_count for s in workbook.worksheets),
        }


class TestSpreadsheetSpecialist:
    """Comprehensive test suite for Spreadsheet Foundation & Specialist."""

    # -------------------------------------------------------------------------
    # 1. Models & Typing
    # -------------------------------------------------------------------------

    def test_workbook_and_worksheet_creation(self):
        """1. Workbook and Worksheet initialization with default metadata."""
        wb = Workbook(title="Q3 Budget Analysis")
        assert wb.title == "Q3 Budget Analysis"
        assert wb.workbook_id.startswith("wb_")
        assert len(wb.worksheets) == 0
        assert wb.metadata.spreadsheet_format == SpreadsheetFormat.CSV

        # Active sheet creates Sheet1 by default
        sheet = wb.active_sheet
        assert sheet.name == "Sheet1"
        assert len(wb.worksheets) == 1
        assert sheet.row_count == 0
        assert sheet.column_count == 0

    def test_required_title_validation(self):
        """2. Title validation enforces non-empty strings."""
        with pytest.raises(ValidationError):
            Workbook(title="")

        with pytest.raises(ValidationError):
            Worksheet(name="")

    def test_cell_type_inference(self):
        """3. Automatic cell type inference for text, number, boolean, formula, empty."""
        c_text = SpreadsheetCell.create(0, 0, "Quarterly Revenue")
        assert c_text.cell_type == CellType.TEXT
        assert c_text.value == "Quarterly Revenue"

        c_num_int = SpreadsheetCell.create(0, 1, 150000)
        assert c_num_int.cell_type == CellType.NUMBER
        assert c_num_int.value == 150000

        c_num_str = SpreadsheetCell.create(0, 2, "42.5")
        assert c_num_str.cell_type == CellType.NUMBER
        assert c_num_str.value == 42.5

        c_bool = SpreadsheetCell.create(0, 3, True)
        assert c_bool.cell_type == CellType.BOOLEAN
        assert c_bool.value is True

        c_bool_str = SpreadsheetCell.create(0, 4, "true")
        assert c_bool_str.cell_type == CellType.BOOLEAN
        assert c_bool_str.value is True

        c_empty = SpreadsheetCell.create(0, 5, "")
        assert c_empty.cell_type == CellType.EMPTY

        c_formula = SpreadsheetCell.create(0, 6, "=SUM(B1:E1)")
        assert c_formula.cell_type == CellType.FORMULA
        assert c_formula.formula == "=SUM(B1:E1)"

    def test_formula_validation_syntax(self):
        """4. Formula cell validation rejects strings not starting with '='."""
        with pytest.raises(ValidationError):
            SpreadsheetCell(row=0, column=0, value="SUM(A1:A5)", formula="SUM(A1:A5)")

    def test_worksheet_cell_manipulation(self):
        """5. Worksheet set_cell, get_cell, and append_row."""
        sheet = Worksheet(name="Data")
        sheet.append_row(["Department", "Headcount", "Budget"])
        sheet.append_row(["Engineering", 25, 500000])

        assert sheet.row_count == 2
        assert sheet.column_count == 3

        c = sheet.get_cell(1, 0)
        assert c is not None
        assert c.value == "Engineering"

        # Dynamically set cell at (3, 2) expanding dimensions
        sheet.set_cell(3, 2, 750000)
        assert sheet.row_count == 4
        assert sheet.get_cell(3, 2).value == 750000

    def test_spreadsheet_template_instantiation(self):
        """6. SpreadsheetTemplate instantiates structured Workbook."""
        tmpl = SpreadsheetTemplate(
            template_name="P&L Statement",
            description="Standard Profit and Loss tabular structure",
            columns=[
                ColumnSpec(name="Category", data_type=CellType.TEXT, required=True),
                ColumnSpec(name="Q1", data_type=CellType.NUMBER),
                ColumnSpec(name="Q2", data_type=CellType.NUMBER),
            ],
            sample_rows=[
                ["Revenue", 100000, 120000],
                ["COGS", 40000, 45000],
            ],
        )

        wb = tmpl.instantiate(title="2026 P&L")
        assert wb.title == "2026 P&L"
        sheet = wb.active_sheet
        assert sheet.row_count == 3  # Header + 2 sample rows
        assert [c.value for c in sheet.rows[0]] == ["Category", "Q1", "Q2"]
        assert sheet.rows[1][1].value == 100000

    # -------------------------------------------------------------------------
    # 2. Builder & Renderers (CSV / TSV)
    # -------------------------------------------------------------------------

    def test_spreadsheet_builder_multi_sheet(self):
        """7. SpreadsheetBuilder supports multi-sheet creation and navigation."""
        builder = SpreadsheetBuilder(title="Consolidated Finances")
        builder.add_row(["Metric", "Total"])
        builder.add_row(["EBITDA", 250000])

        builder.add_worksheet("Regional")
        builder.add_row(["Region", "Revenue"])
        builder.add_row(["North America", 150000])
        builder.add_row(["EMEA", 100000])

        wb = builder.build()
        assert len(wb.worksheets) == 2
        assert wb.worksheets[0].name == "Sheet1"
        assert wb.worksheets[1].name == "Regional"
        assert wb.worksheets[1].row_count == 3

    def test_csv_rendering_and_parsing_roundtrip(self):
        """8. CSVSpreadsheetRenderer and Parser roundtrip."""
        adapter = DevTestSpreadsheetAdapter()
        headers = ["ID", "Item", "Price", "InStock"]
        rows = [
            [101, "Widget A", 19.99, True],
            [102, "Widget B", 49.50, False],
        ]
        wb = adapter.create_simple_sheet("Inventory", headers, rows)

        csv_str = adapter.renderer.render(wb, delimiter=",")
        assert "ID,Item,Price,InStock" in csv_str
        assert "101,Widget A,19.99,True" in csv_str

        parsed_wb = adapter.parser.parse(csv_str, delimiter=",", metadata={"title": "Parsed Inventory"})
        assert parsed_wb.title == "Parsed Inventory"
        sheet = parsed_wb.active_sheet
        assert sheet.row_count == 3
        assert sheet.rows[1][0].value == 101
        assert sheet.rows[1][2].value == 19.99
        assert sheet.rows[1][3].value is True

    def test_tsv_rendering_and_parsing(self):
        """9. TSV rendering and parsing with tab delimiters."""
        adapter = DevTestSpreadsheetAdapter()
        wb = adapter.create_simple_sheet("Tabular TSV", ["Col1", "Col2"], [["Val1", "Val2"]])

        tsv_str = adapter.renderer.render(wb, delimiter="\t")
        assert "Col1\tCol2\n" in tsv_str
        assert "Val1\tVal2\n" in tsv_str

        parsed = adapter.parser.parse(tsv_str, delimiter="\t")
        assert parsed.active_sheet.row_count == 2
        assert parsed.metadata.spreadsheet_format == SpreadsheetFormat.TSV

    # -------------------------------------------------------------------------
    # 3. Specialist Metadata & Interface Conformance
    # -------------------------------------------------------------------------

    def test_specialist_interface_conformance(self):
        """10. ISpreadsheetSpecialist interface contract implementation."""
        specialist = DummySpreadsheetSpecialist()
        wb = specialist.synthesize_spreadsheet(
            title="Q3 Strategy",
            topic="Growth Metrics",
            columns=["KPI", "Target"],
            rows=[["CAC", 150]],
        )
        assert wb.title == "Q3 Strategy"
        assert wb.active_sheet.row_count == 2

        edited = specialist.edit_spreadsheet(
            workbook=wb,
            instructions="Update target",
            edits={"set_cell": {"row": 1, "column": 1, "value": 120}},
        )
        assert edited.active_sheet.rows[1][1].value == 120

        val = specialist.validate_spreadsheet(edited)
        assert val["valid"] is True
        assert val["total_rows"] == 2

    def test_create_spreadsheet_specialist_metadata(self):
        """11. Factory generates authoritative SpecialistMetadata with all capabilities."""
        meta = create_spreadsheet_specialist()
        assert meta.specialist_id == "spec_spreadsheet_01"
        assert meta.name == "Spreadsheet Specialist"
        assert meta.status == SpecialistStatus.ACTIVE
        assert meta.security_level == "standard"
        assert "file_service" in meta.authorized_tools
        assert "spreadsheet_builder" in meta.authorized_tools
        assert "spreadsheet_parser" in meta.authorized_tools
        assert "spreadsheet_validator" in meta.authorized_tools

        caps = {c.name: c for c in meta.capabilities}
        assert "spreadsheet_generation" in caps
        assert "spreadsheet_editing" in caps
        assert "spreadsheet_validation" in caps

        assert caps["spreadsheet_generation"].required_tools == ["file_service"]
        assert caps["spreadsheet_editing"].required_tools == ["file_service"]
        assert caps["spreadsheet_validation"].required_tools == ["spreadsheet_validator"]
        assert meta.provenance.registry_id == "local_dev_registry"

    # -------------------------------------------------------------------------
    # 4. Capability Handlers (Generation, Editing, Validation)
    # -------------------------------------------------------------------------

    def test_spreadsheet_generation_with_file_service(self):
        """12. Spreadsheet generation persists CSV artifact through FileService."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_sheet_test")

        handler = SpreadsheetGenerationCapabilityHandler(file_adapter=file_adapter)
        meta = create_spreadsheet_specialist()
        req = make_delegation_request(
            delegation_id="del_sheet_gen_01",
            capability_name="spreadsheet_generation",
            inputs={
                "title": "Marketing Campaign Performance",
                "workspace_id": "ws_sheet_test",
                "relative_path": "finance/campaign_roi.csv",
                "headers": ["Campaign", "Spend", "Conversions", "CPA"],
                "rows": [
                    ["Q3 Launch", 5000, 120, 41.67],
                    ["Brand Awareness", 3000, 45, 66.67],
                ],
            },
        )

        output = handler.execute(req, meta)
        assert output.success is True
        assert len(output.artifacts) == 1
        assert "finance/campaign_roi.csv" in output.artifacts[0]
        assert len(output.facts) == 1
        assert output.facts[0].source == "spreadsheet_specialist"

        # Verify file persisted inside workspace
        fs = file_adapter.get_file_service("ws_sheet_test")
        read_res = fs.read_file("finance/campaign_roi.csv")
        assert read_res.success is True
        assert "Campaign,Spend,Conversions,CPA" in read_res.content
        assert "Q3 Launch,5000,120,41.67" in read_res.content

    def test_spreadsheet_editing_operations(self):
        """13. Spreadsheet editing modifies cells, appends rows, and preserves unrelated data."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_sheet_edit")
        fs = file_adapter.get_file_service("ws_sheet_edit")

        # Initial CSV
        initial_csv = "Item,Price,Stock\nApples,2.50,100\nOranges,3.00,80\n"
        fs.create_file("inventory.csv", initial_csv, overwrite=True)

        handler = SpreadsheetEditingCapabilityHandler(file_adapter=file_adapter)
        meta = create_spreadsheet_specialist()

        # 1. Update cell: change Apples price from 2.50 to 2.75 at (1, 1)
        req1 = make_delegation_request(
            delegation_id="del_sheet_edit_01",
            capability_name="spreadsheet_editing",
            inputs={
                "relative_path": "inventory.csv",
                "workspace_id": "ws_sheet_edit",
                "action": "set_cell",
                "row": 1,
                "column": 1,
                "value": 2.75,
            },
        )
        res1 = handler.execute(req1, meta)
        assert res1.success is True

        read1 = fs.read_file("inventory.csv")
        assert "Apples,2.75,100" in read1.content
        assert "Oranges,3.0,80" in read1.content or "Oranges,3.00,80" in read1.content

        # 2. Append row
        req2 = make_delegation_request(
            delegation_id="del_sheet_edit_02",
            capability_name="spreadsheet_editing",
            inputs={
                "relative_path": "inventory.csv",
                "workspace_id": "ws_sheet_edit",
                "action": "append_row",
                "values": ["Bananas", 1.99, 150],
            },
        )
        res2 = handler.execute(req2, meta)
        assert res2.success is True

        read2 = fs.read_file("inventory.csv")
        assert "Bananas,1.99,150" in read2.content

        # 3. Add column: 'Supplier'
        req3 = make_delegation_request(
            delegation_id="del_sheet_edit_03",
            capability_name="spreadsheet_editing",
            inputs={
                "relative_path": "inventory.csv",
                "workspace_id": "ws_sheet_edit",
                "action": "add_column",
                "name": "Supplier",
                "values": ["FarmFresh", "CitrusCo", "TropicalImports"],
            },
        )
        res3 = handler.execute(req3, meta)
        assert res3.success is True

        read3 = fs.read_file("inventory.csv")
        assert "Item,Price,Stock,Supplier" in read3.content
        assert "Apples,2.75,100,FarmFresh" in read3.content
        assert "Bananas,1.99,150,TropicalImports" in read3.content

    def test_spreadsheet_editing_file_not_found(self):
        """14. Spreadsheet editing cleanly reports non-existent file."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_sheet_edit")

        handler = SpreadsheetEditingCapabilityHandler(file_adapter=file_adapter)
        meta = create_spreadsheet_specialist()
        req = make_delegation_request(
            delegation_id="del_sheet_edit_err",
            capability_name="spreadsheet_editing",
            inputs={
                "relative_path": "missing_sheet.csv",
                "workspace_id": "ws_sheet_edit",
                "action": "set_cell",
                "row": 0,
                "col": 0,
                "value": "Test",
            },
        )
        res = handler.execute(req, meta)
        assert res.success is False
        assert "SPREADSHEET_NOT_FOUND" in res.output_text

    def test_spreadsheet_validation_success_and_evidence(self):
        """15. Spreadsheet validation accepts valid workbook and produces VerificationEvidence."""
        handler = SpreadsheetValidationCapabilityHandler()
        meta = create_spreadsheet_specialist()

        wb = (
            SpreadsheetBuilder(title="Operational Audit")
            .add_row(["Task", "Assignee", "Status", "Effort"])
            .add_row(["Security Sandbox", "Dev Specialist", "DONE", 4])
            .add_row(["Spreadsheet Engine", "Spreadsheet Specialist", "IN_PROGRESS", 6])
            .build()
        )

        req = make_delegation_request(
            delegation_id="del_sheet_val_01",
            capability_name="spreadsheet_validation",
            inputs={
                "spreadsheet": wb,
                "min_rows": 2,
                "min_columns": 3,
                "required_columns": ["Task", "Status"],
            },
        )

        res = handler.execute(req, meta)
        assert res.success is True
        assert "successfully verified" in res.output_text
        assert len(res.additional_evidence) == 1
        assert isinstance(res.additional_evidence[0], VerificationEvidence)
        assert res.additional_evidence[0].verified_status == "VERIFIED"

    def test_spreadsheet_validation_failures_and_non_mutating(self):
        """16. Spreadsheet validation rejects missing columns and does not mutate source."""
        handler = SpreadsheetValidationCapabilityHandler()
        meta = create_spreadsheet_specialist()

        wb = (
            SpreadsheetBuilder(title="Incomplete Sheet")
            .add_row(["ColA", "ColB"])
            .add_row([1, 2])
            .build()
        )

        # Missing required column 'ColC'
        req = make_delegation_request(
            delegation_id="del_sheet_val_02",
            capability_name="spreadsheet_validation",
            inputs={
                "spreadsheet": wb,
                "required_columns": ["ColA", "ColC"],
            },
        )
        res = handler.execute(req, meta)
        assert res.success is False
        assert any("missing required column 'ColC'" in err for err in res.errors)

        # Verify source workbook was NOT mutated
        assert wb.title == "Incomplete Sheet"
        assert wb.active_sheet.row_count == 2
        assert len(wb.active_sheet.rows[0]) == 2

    # -------------------------------------------------------------------------
    # 5. Full Real Registry & SpecialistExecutionEngine Integration
    # -------------------------------------------------------------------------

    def test_specialist_execution_engine_end_to_end_dispatch(self):
        """17. Full SpecialistExecutionEngine dispatch to Spreadsheet Specialist."""
        registry = InMemorySpecialistRegistryAdapter()
        meta = create_spreadsheet_specialist()
        registry.register_specialist(meta)

        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_engine_sheet")

        engine = SpecialistExecutionEngine(registry_client=registry)
        gen_handler = SpreadsheetGenerationCapabilityHandler(file_adapter=file_adapter)
        edit_handler = SpreadsheetEditingCapabilityHandler(file_adapter=file_adapter)
        val_handler = SpreadsheetValidationCapabilityHandler()

        engine.register_handler(gen_handler)
        engine.register_handler(edit_handler)
        engine.register_handler(val_handler)

        # 1. Execute spreadsheet generation
        gen_req = make_delegation_request(
            delegation_id="del_eng_sheet_01",
            capability_name="spreadsheet_generation",
            inputs={
                "title": "Quarterly Sales Pipeline",
                "workspace_id": "ws_engine_sheet",
                "relative_path": "sales/pipeline.csv",
                "headers": ["Deal", "Value", "Stage"],
                "rows": [
                    ["Deal Alpha", 50000, "Qualified"],
                    ["Deal Beta", 75000, "Proposal"],
                ],
            },
        )
        gen_result = engine.execute_delegation(gen_req)
        assert gen_result.status == "SUCCESS"
        assert len(gen_result.artifacts) == 1
        assert gen_result.evidence.contains_category(EvidenceCategory.ARTIFACT)

        # 2. Execute spreadsheet editing
        edit_req = make_delegation_request(
            delegation_id="del_eng_sheet_02",
            capability_name="spreadsheet_editing",
            inputs={
                "relative_path": "sales/pipeline.csv",
                "workspace_id": "ws_engine_sheet",
                "action": "append_row",
                "values": ["Deal Gamma", 120000, "Negotiation"],
            },
        )
        edit_result = engine.execute_delegation(edit_req)
        assert edit_result.status == "SUCCESS"
        assert "sales/pipeline.csv" in edit_result.output

        # 3. Read edited file and validate
        fs = file_adapter.get_file_service("ws_engine_sheet")
        read_file = fs.read_file("sales/pipeline.csv")
        parser = CSVSpreadsheetParser()
        parsed_wb = parser.parse(read_file.content)

        val_req = make_delegation_request(
            delegation_id="del_eng_sheet_03",
            capability_name="spreadsheet_validation",
            inputs={"spreadsheet": parsed_wb, "min_rows": 4},
        )
        val_result = engine.execute_delegation(val_req)
        assert val_result.status == "SUCCESS"
        assert val_result.evidence.contains_category(EvidenceCategory.VERIFICATION)

    def test_specialist_execution_engine_unauthorized_capability_rejection(self):
        """18. Execution engine rejects capabilities not registered for Spreadsheet Specialist."""
        registry = InMemorySpecialistRegistryAdapter()
        meta = create_spreadsheet_specialist()
        registry.register_specialist(meta)

        engine = SpecialistExecutionEngine(registry_client=registry)
        gen_handler = SpreadsheetGenerationCapabilityHandler()
        engine.register_handler(gen_handler)

        req = make_delegation_request(
            delegation_id="del_eng_sheet_unauth",
            capability_name="unauthorized_spreadsheet_op",
            inputs={"title": "Test"},
        )
        result = engine.execute_delegation(req)
        assert result.status == "FAILED"
        assert "CAPABILITY" in result.output
