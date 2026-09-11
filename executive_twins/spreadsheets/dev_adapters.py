import csv
import io
from typing import Any, Dict, List, Optional, Union
import uuid

from executive_twins.schemas.common import SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    RegistryProvenance,
    SpecialistMetadata,
)
from executive_twins.spreadsheets.interfaces import (
    ISpreadsheetBuilder,
    ISpreadsheetParser,
    ISpreadsheetRenderer,
)
from executive_twins.spreadsheets.models import (
    CellType,
    SpreadsheetCell,
    SpreadsheetFormat,
    SpreadsheetMetadata,
    Workbook,
    Worksheet,
)


class SpreadsheetBuilder(ISpreadsheetBuilder):
    """
    Standard in-memory implementation of ISpreadsheetBuilder.
    Provides fluent, declarative assembly of Workbook and Worksheet models.
    """

    def __init__(self, title: Optional[str] = None) -> None:
        self._title: str = title or "Untitled Workbook"
        self._metadata: SpreadsheetMetadata = SpreadsheetMetadata()
        self._worksheets: List[Worksheet] = []
        self._active_sheet_idx: int = 0

        # Initialize with one default sheet
        default_sheet = Worksheet(name="Sheet1")
        self._worksheets.append(default_sheet)

    def set_title(self, title: str) -> "SpreadsheetBuilder":
        if not title or not title.strip():
            raise ValueError("Workbook title cannot be empty.")
        self._title = title.strip()
        return self

    def set_metadata(self, metadata: SpreadsheetMetadata) -> "SpreadsheetBuilder":
        self._metadata = metadata
        return self

    def add_worksheet(self, name: str) -> "SpreadsheetBuilder":
        if not name or not name.strip():
            raise ValueError("Worksheet name cannot be empty.")
        sheet = Worksheet(name=name.strip())
        self._worksheets.append(sheet)
        self._active_sheet_idx = len(self._worksheets) - 1
        return self

    def set_active_worksheet(self, name_or_idx: Union[str, int]) -> "SpreadsheetBuilder":
        if isinstance(name_or_idx, int):
            if 0 <= name_or_idx < len(self._worksheets):
                self._active_sheet_idx = name_or_idx
                return self
            raise IndexError(f"Worksheet index {name_or_idx} out of range.")
        target = str(name_or_idx).strip().lower()
        for idx, s in enumerate(self._worksheets):
            if s.name.strip().lower() == target:
                self._active_sheet_idx = idx
                return self
        raise KeyError(f"Worksheet named '{name_or_idx}' not found.")

    def _get_active_sheet(self) -> Worksheet:
        if not self._worksheets:
            self._worksheets.append(Worksheet(name="Sheet1"))
            self._active_sheet_idx = 0
        return self._worksheets[self._active_sheet_idx]

    def add_row(self, values: List[Any]) -> "SpreadsheetBuilder":
        sheet = self._get_active_sheet()
        sheet.append_row(values)
        return self

    def set_cell(
        self,
        row: int,
        column: int,
        value: Any,
        formula: Optional[str] = None,
    ) -> "SpreadsheetBuilder":
        sheet = self._get_active_sheet()
        sheet.set_cell(row, column, value, formula=formula)
        return self

    def build(self) -> Workbook:
        if not self._title or not self._title.strip():
            raise ValueError("Cannot build Workbook: title is required.")

        return Workbook(
            title=self._title,
            worksheets=list(self._worksheets),
            metadata=self._metadata,
        )

    def reset(self) -> "SpreadsheetBuilder":
        self._title = "Untitled Workbook"
        self._metadata = SpreadsheetMetadata()
        self._worksheets = [Worksheet(name="Sheet1")]
        self._active_sheet_idx = 0
        return self


class CSVSpreadsheetRenderer(ISpreadsheetRenderer):
    """
    Pure Python deterministic renderer that converts Workbook models into CSV or TSV string representation.
    """

    def render(
        self,
        workbook: Workbook,
        sheet_name_or_idx: Optional[Union[str, int]] = None,
        delimiter: str = ",",
    ) -> str:
        if sheet_name_or_idx is not None:
            sheet = workbook.get_sheet(sheet_name_or_idx)
            if sheet is None:
                raise KeyError(f"Worksheet '{sheet_name_or_idx}' not found in workbook.")
        else:
            sheet = workbook.active_sheet

        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")

        for row in sheet.rows:
            row_values = []
            for cell in row:
                if cell.cell_type == CellType.FORMULA and cell.formula:
                    row_values.append(cell.formula)
                elif cell.value is None:
                    row_values.append("")
                else:
                    row_values.append(str(cell.value))
            writer.writerow(row_values)

        return output.getvalue()


class CSVSpreadsheetParser(ISpreadsheetParser):
    """
    Pure Python deterministic parser converting CSV / TSV text into structured Workbook models.
    """

    def parse(
        self,
        content: str,
        delimiter: str = ",",
        sheet_name: str = "Sheet1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Workbook:
        title = "Parsed Spreadsheet"
        if metadata and "title" in metadata:
            title = str(metadata["title"])

        format_type = SpreadsheetFormat.TSV if delimiter == "\t" else SpreadsheetFormat.CSV
        meta = SpreadsheetMetadata(
            spreadsheet_format=format_type,
            custom_attributes=metadata or {},
        )

        wb = Workbook(title=title, metadata=meta)
        sheet = wb.active_sheet
        sheet.name = sheet_name

        input_stream = io.StringIO(content)
        reader = csv.reader(input_stream, delimiter=delimiter)

        for row_idx, raw_row in enumerate(reader):
            cell_list: List[SpreadsheetCell] = []
            for col_idx, raw_val in enumerate(raw_row):
                cell = SpreadsheetCell.create(row=row_idx, column=col_idx, value=raw_val)
                cell_list.append(cell)
            sheet.rows.append(cell_list)

        return wb


class DevTestSpreadsheetAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Convenience adapter grouping SpreadsheetBuilder, Renderer, and Parser.
    """

    def __init__(self) -> None:
        self.builder = SpreadsheetBuilder()
        self.renderer = CSVSpreadsheetRenderer()
        self.parser = CSVSpreadsheetParser()

    def create_simple_sheet(
        self,
        title: str,
        headers: List[str],
        rows: List[List[Any]],
    ) -> Workbook:
        builder = SpreadsheetBuilder(title=title)
        builder.add_row(headers)
        for r in rows:
            builder.add_row(r)
        return builder.build()


def create_spreadsheet_specialist(
    specialist_id: str = "spec_spreadsheet_01",
    name: str = "Spreadsheet Specialist",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for the Spreadsheet Specialist.
    Declares all supported spreadsheet capabilities and authorized tools into the registry.
    """
    capabilities = [
        Capability(
            name="spreadsheet_generation",
            description="Controlled synthesis of structured workbooks and tabular data artifacts",
            required_tools=["file_service"],
        ),
        Capability(
            name="spreadsheet_editing",
            description="Controlled structured workbook modification, cell updates, and row/column editing",
            required_tools=["file_service"],
        ),
        Capability(
            name="spreadsheet_validation",
            description="Controlled structural, dimensional, and formula validation for workbooks",
            required_tools=["spreadsheet_validator"],
        ),
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=["file_service", "spreadsheet_builder", "spreadsheet_parser", "spreadsheet_validator"],
        security_level=security_level,
        provenance=RegistryProvenance(
            registry_id="local_dev_registry",
            snapshot_id="snap_spreadsheet_v1",
        ),
    )
