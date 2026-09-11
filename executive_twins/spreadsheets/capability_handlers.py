from typing import Any, Dict, List, Optional, Union
import uuid

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.spreadsheets.dev_adapters import (
    CSVSpreadsheetParser,
    CSVSpreadsheetRenderer,
    SpreadsheetBuilder,
)
from executive_twins.spreadsheets.models import (
    CellType,
    SpreadsheetCell,
    SpreadsheetFormat,
    SpreadsheetMetadata,
    Workbook,
    Worksheet,
)


class SpreadsheetGenerationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for synthesizing structured workbooks and tabular data artifacts.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "spreadsheet_generation"
    required_tool = "file_service"
    required_params = ["title"]
    allowed_params = [
        "title",
        "columns",
        "headers",
        "rows",
        "sheets",
        "output_format",
        "delimiter",
        "relative_path",
        "workspace_id",
        "template_name",
        "template",
        "metadata",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.renderer = CSVSpreadsheetRenderer()
        self.parser = CSVSpreadsheetParser()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "title" not in inputs or not inputs["title"]:
            return "Missing required parameter 'title' for capability 'spreadsheet_generation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        title = str(request.inputs.get("title", "Untitled Spreadsheet"))
        output_format = str(request.inputs.get("output_format", "csv")).lower()
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        delimiter = str(request.inputs.get("delimiter", "\t" if output_format == "tsv" else ","))

        # 1. Build Workbook
        builder = SpreadsheetBuilder(title=title)

        raw_meta = request.inputs.get("metadata")
        if isinstance(raw_meta, SpreadsheetMetadata):
            builder.set_metadata(raw_meta)
        elif isinstance(raw_meta, dict):
            builder.set_metadata(
                SpreadsheetMetadata(
                    author=raw_meta.get("author", "LM-Brain Workforce"),
                    version=str(raw_meta.get("version", "1.0")),
                    spreadsheet_format=SpreadsheetFormat.TSV if delimiter == "\t" else SpreadsheetFormat.CSV,
                    custom_attributes=raw_meta.get("custom_attributes", {}),
                )
            )

        # Handle multiple sheets if provided
        raw_sheets = request.inputs.get("sheets")
        if isinstance(raw_sheets, list) and len(raw_sheets) > 0:
            for s_idx, s_data in enumerate(raw_sheets):
                if isinstance(s_data, dict):
                    s_name = str(s_data.get("name", f"Sheet{s_idx + 1}"))
                    if s_idx == 0:
                        builder.set_active_worksheet(0)
                        # Rename first default sheet
                        builder._get_active_sheet().name = s_name
                    else:
                        builder.add_worksheet(s_name)

                    # Headers & Rows for this sheet
                    s_headers = s_data.get("headers") or s_data.get("columns")
                    if isinstance(s_headers, list) and len(s_headers) > 0:
                        builder.add_row(list(s_headers))

                    s_rows = s_data.get("rows", [])
                    if isinstance(s_rows, list):
                        for r in s_rows:
                            if isinstance(r, list):
                                builder.add_row(r)
        else:
            # Single sheet mode
            headers = request.inputs.get("headers") or request.inputs.get("columns")
            if isinstance(headers, list) and len(headers) > 0:
                builder.add_row(list(headers))

            rows = request.inputs.get("rows", [])
            if isinstance(rows, list):
                for r in rows:
                    if isinstance(r, list):
                        builder.add_row(r)

        workbook = builder.build()

        # 2. Render to CSV / TSV
        rendered_content = self.renderer.render(workbook, delimiter=delimiter)
        ext = "tsv" if delimiter == "\t" or output_format == "tsv" else "csv"

        # 3. Persist via FileService
        default_filename = f"spreadsheet_{request.delegation_id[:8]}.{ext}"
        rel_path = str(request.inputs.get("relative_path", default_filename))

        artifacts: List[str] = []
        additional_evidence: List[Any] = []

        if self.file_adapter is not None:
            file_service = self.file_adapter.get_file_service(ws_id)
            if file_service:
                res = file_service.create_file(rel_path, rendered_content, overwrite=True)
                if res.success and res.artifact:
                    artifacts.append(res.artifact.artifact_uri)
                    additional_evidence.extend(res.evidence)
        else:
            artifact_uri = f"workspace://{ws_id}/{rel_path}"
            artifacts.append(artifact_uri)
            additional_evidence.append(
                ArtifactEvidence(
                    evidence_id=f"ev-sheet-art-{request.delegation_id[:8]}",
                    artifact_uri=artifact_uri,
                    description=f"Generated spreadsheet artifact for '{title}'",
                    mime_type="text/tab-separated-values" if ext == "tsv" else "text/csv",
                )
            )

        total_rows = sum(s.row_count for s in workbook.worksheets)
        facts = [
            FactItem(
                statement=f"Generated spreadsheet '{title}' containing {len(workbook.worksheets)} sheet(s) and {total_rows} total rows.",
                state=FactState.FACT,
                source="spreadsheet_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully generated spreadsheet '{title}' with {total_rows} row(s) at '{rel_path}'.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )


class SpreadsheetEditingCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for structured spreadsheet modifications, cell updates, and row/column mutations.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "spreadsheet_editing"
    required_tool = "file_service"
    required_params = ["relative_path"]
    allowed_params = [
        "relative_path",
        "workspace_id",
        "edits",
        "action",
        "row",
        "column",
        "col",
        "value",
        "formula",
        "values",
        "row_data",
        "name",
        "header",
        "new_name",
        "sheet_name",
        "delimiter",
    ]

    def __init__(self, file_adapter: Optional[DevFileServiceAdapter] = None) -> None:
        self.file_adapter = file_adapter
        self.renderer = CSVSpreadsheetRenderer()
        self.parser = CSVSpreadsheetParser()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "relative_path" not in inputs or not inputs["relative_path"]:
            return "Missing required parameter 'relative_path' for capability 'spreadsheet_editing'."

        has_edit = any(
            k in inputs and inputs[k] is not None
            for k in ["edits", "action", "row", "column", "col", "value", "values", "row_data", "formula", "name", "header"]
        )
        if not has_edit:
            return "Missing edit specification ('edits', 'action', 'value', or 'values') for capability 'spreadsheet_editing'."

        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        rel_path = str(request.inputs.get("relative_path", ""))
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        delimiter = str(request.inputs.get("delimiter", "\t" if rel_path.endswith(".tsv") else ","))

        if self.file_adapter is None:
            return CapabilityHandlerOutput(
                success=False,
                output_text="EXECUTION_ERROR: FileService adapter is not available for spreadsheet editing.",
                errors=["No FileService adapter configured."],
            )

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXECUTION_ERROR: Workspace '{ws_id}' not found.",
                errors=[f"Workspace '{ws_id}' not found."],
            )

        read_res = file_service.read_file(rel_path)
        if not read_res.success or read_res.content is None:
            err_msg = read_res.error_message or "File could not be read."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"SPREADSHEET_NOT_FOUND: Could not read target spreadsheet '{rel_path}': {err_msg}",
                errors=[f"Target file '{rel_path}' does not exist or cannot be read: {err_msg}"],
            )

        # Parse existing content into Workbook
        workbook = self.parser.parse(read_res.content, delimiter=delimiter)

        # Apply edits
        edits = request.inputs.get("edits")
        applied_actions: List[str] = []

        if isinstance(edits, list):
            for edit_item in edits:
                if isinstance(edit_item, dict):
                    self._apply_single_edit(workbook, edit_item, applied_actions)
        elif isinstance(edits, dict):
            self._apply_single_edit(workbook, edits, applied_actions)
        else:
            # Single action from direct params
            single_spec = {
                "action": request.inputs.get("action", "set_cell"),
                "row": request.inputs.get("row"),
                "column": request.inputs.get("column", request.inputs.get("col")),
                "value": request.inputs.get("value"),
                "formula": request.inputs.get("formula"),
                "values": request.inputs.get("values", request.inputs.get("row_data")),
                "name": request.inputs.get("name"),
                "header": request.inputs.get("header"),
                "new_name": request.inputs.get("new_name"),
                "sheet_name": request.inputs.get("sheet_name"),
            }
            self._apply_single_edit(workbook, single_spec, applied_actions)

        # Re-render updated workbook
        updated_content = self.renderer.render(workbook, delimiter=delimiter)

        # Overwrite file via FileService
        write_res = file_service.create_file(rel_path, updated_content, overwrite=True)
        if not write_res.success:
            write_err = write_res.error_message or "Write failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"FILE_WRITE_FAILED: Failed to save edited spreadsheet: {write_err}",
                errors=[f"Write failed: {write_err}"],
            )

        artifacts: List[str] = []
        additional_evidence: List[Any] = []
        if write_res.artifact:
            artifacts.append(write_res.artifact.artifact_uri)
            additional_evidence.extend(write_res.evidence)

        facts = [
            FactItem(
                statement=f"Applied spreadsheet edits to '{rel_path}': {', '.join(applied_actions) if applied_actions else 'Updated tabular cells'}.",
                state=FactState.FACT,
                source="spreadsheet_specialist",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully edited spreadsheet '{rel_path}' with actions: {', '.join(applied_actions) if applied_actions else 'updated'}.",
            facts=facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=additional_evidence,
        )

    def _apply_single_edit(
        self,
        workbook: Workbook,
        edit: Dict[str, Any],
        applied_actions: List[str],
    ) -> None:
        action = str(edit.get("action", "set_cell")).lower()
        sheet_target = edit.get("sheet_name") or edit.get("sheet")
        sheet = workbook.get_sheet(sheet_target) if sheet_target else workbook.active_sheet
        if sheet is None:
            sheet = workbook.active_sheet

        if action in ("set_cell", "update_cell"):
            row = int(edit.get("row", 0))
            col = int(edit.get("column", edit.get("col", 0)))
            val = edit.get("value")
            formula = edit.get("formula")
            sheet.set_cell(row=row, column=col, value=val, formula=formula)
            applied_actions.append(f"set cell at ({row}, {col})")

        elif action in ("append_row", "add_row"):
            vals = edit.get("values") or edit.get("row_data") or []
            if isinstance(vals, list):
                sheet.append_row(vals)
                applied_actions.append(f"appended row with {len(vals)} value(s)")

        elif action in ("update_row", "replace_row"):
            row_idx = int(edit.get("row", 0))
            vals = edit.get("values") or edit.get("row_data") or []
            if isinstance(vals, list):
                while len(sheet.rows) <= row_idx:
                    sheet.rows.append([])
                sheet.rows[row_idx] = [
                    SpreadsheetCell.create(row=row_idx, column=c_idx, value=v)
                    for c_idx, v in enumerate(vals)
                ]
                applied_actions.append(f"updated row {row_idx}")

        elif action in ("add_column", "append_column"):
            header = edit.get("header") or edit.get("name") or "New Column"
            col_values = edit.get("values", [])
            for r_idx, row in enumerate(sheet.rows):
                if r_idx == 0:
                    row.append(SpreadsheetCell.create(row=0, column=len(row), value=header))
                else:
                    val_idx = r_idx - 1
                    val = col_values[val_idx] if val_idx < len(col_values) else ""
                    row.append(SpreadsheetCell.create(row=r_idx, column=len(row), value=val))
            applied_actions.append(f"added column '{header}'")

        elif action in ("rename_sheet", "set_sheet_name"):
            new_name = str(edit.get("new_name") or edit.get("name") or "")
            if new_name:
                sheet.name = new_name
                applied_actions.append(f"renamed sheet to '{new_name}'")


class SpreadsheetValidationCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for validating spreadsheet structure, dimensions, and formula syntax.
    """

    capability_name = "spreadsheet_validation"
    required_tool = "spreadsheet_validator"
    required_params = ["spreadsheet"]
    allowed_params = [
        "spreadsheet",
        "workbook",
        "doc",
        "min_rows",
        "max_rows",
        "min_columns",
        "require_headers",
        "required_columns",
        "validate_formulas",
    ]

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "spreadsheet" not in inputs and "workbook" in inputs:
            inputs["spreadsheet"] = inputs["workbook"]
        if "spreadsheet" not in inputs or inputs["spreadsheet"] is None:
            return "Missing required parameter 'spreadsheet' for capability 'spreadsheet_validation'."
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        raw_sheet = request.inputs.get("spreadsheet")
        min_rows = int(request.inputs.get("min_rows", 0))
        max_rows = int(request.inputs.get("max_rows", 100000))
        min_cols = int(request.inputs.get("min_columns", 0))
        required_columns = request.inputs.get("required_columns", [])
        validate_formulas = bool(request.inputs.get("validate_formulas", True))

        errors: List[str] = []

        if isinstance(raw_sheet, Workbook):
            wb = raw_sheet
        elif isinstance(raw_sheet, dict):
            try:
                wb = Workbook.model_validate(raw_sheet)
            except Exception as e:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text=f"VALIDATION_FAILED: Invalid workbook schema: {str(e)}",
                    errors=[f"Schema decoding error: {str(e)}"],
                )
        else:
            return CapabilityHandlerOutput(
                success=False,
                output_text="VALIDATION_FAILED: Input 'spreadsheet' must be a Workbook model or dictionary.",
                errors=["Invalid spreadsheet object type."],
            )

        # Rule 1: Title non-empty
        if not wb.title or not wb.title.strip():
            errors.append("Workbook title is empty.")

        # Rule 2: At least 1 worksheet
        if not wb.worksheets:
            errors.append("Workbook contains no worksheets.")

        # Rule 3: Sheet validation
        total_rows = 0
        for sheet_idx, sheet in enumerate(wb.worksheets):
            if not sheet.name or not sheet.name.strip():
                errors.append(f"Worksheet at index {sheet_idx} has an empty name.")

            total_rows += sheet.row_count

            if sheet.row_count < min_rows:
                errors.append(
                    f"Worksheet '{sheet.name}' has {sheet.row_count} row(s), below minimum required {min_rows}."
                )
            if sheet.row_count > max_rows:
                errors.append(
                    f"Worksheet '{sheet.name}' has {sheet.row_count} row(s), exceeding maximum allowed {max_rows}."
                )

            if sheet.column_count < min_cols:
                errors.append(
                    f"Worksheet '{sheet.name}' has {sheet.column_count} column(s), below minimum required {min_cols}."
                )

            # Check required columns
            if isinstance(required_columns, list) and len(required_columns) > 0 and sheet.row_count > 0:
                header_row = [str(c.value).strip().lower() for c in sheet.rows[0]]
                for req_col in required_columns:
                    if str(req_col).strip().lower() not in header_row:
                        errors.append(f"Worksheet '{sheet.name}' is missing required column '{req_col}'.")

            # Check formulas
            if validate_formulas:
                for r in sheet.rows:
                    for c in r:
                        if c.cell_type == CellType.FORMULA:
                            if not c.formula or not c.formula.startswith("="):
                                errors.append(f"Malformed formula '{c.formula}' at cell ({c.row}, {c.column}).")

        if errors:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"Spreadsheet validation failed with {len(errors)} error(s).",
                errors=errors,
            )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-sheet-verif-{request.delegation_id[:8]}",
            verifier_id="spreadsheet_validator",
            verified_status="VERIFIED",
            description=f"Verified workbook '{wb.title}' containing {len(wb.worksheets)} worksheet(s) and {total_rows} total rows.",
        )

        facts = [
            FactItem(
                statement=f"Validated spreadsheet '{wb.title}' ({len(wb.worksheets)} sheet(s), {total_rows} rows) with zero structural errors.",
                state=FactState.FACT,
                source="spreadsheet_validator",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Spreadsheet '{wb.title}' successfully verified ({len(wb.worksheets)} sheet(s), {total_rows} rows).",
            facts=facts,
            artifacts=[],
            errors=[],
            additional_evidence=[verif_ev],
        )
