"""
Spreadsheet Foundation Domain Models.
Provides typed, provider-independent models for Workbooks, Worksheets, Cells,
Formulas, and Templates.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field, field_validator


class CellType(str, Enum):
    """Supported deterministic cell data types."""
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    FORMULA = "FORMULA"
    EMPTY = "EMPTY"


class SpreadsheetFormat(str, Enum):
    """Supported tabular output and storage formats."""
    CSV = "CSV"
    TSV = "TSV"


class SpreadsheetCell(BaseModel):
    """
    Represents an atomic typed cell in a spreadsheet.
    """
    row: int = Field(ge=0, description="0-indexed row position")
    column: int = Field(ge=0, description="0-indexed column position")
    value: Any = Field(default=None, description="Raw cell value")
    cell_type: CellType = Field(default=CellType.TEXT, description="Inferred or declared cell type")
    formula: Optional[str] = Field(default=None, description="Optional formula string (e.g. '=SUM(A1:A5)')")

    @field_validator("formula")
    @classmethod
    def validate_formula_syntax(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_strip = v.strip()
            if not v_strip.startswith("="):
                raise ValueError("Spreadsheet formula must begin with '='.")
            return v_strip
        return v

    @classmethod
    def create(
        cls,
        row: int,
        column: int,
        value: Any,
        cell_type: Optional[CellType] = None,
        formula: Optional[str] = None,
    ) -> "SpreadsheetCell":
        """Convenience factory with automatic type inference."""
        if formula is not None or (isinstance(value, str) and value.strip().startswith("=")):
            f_val = formula or str(value).strip()
            return cls(
                row=row,
                column=column,
                value=f_val,
                cell_type=CellType.FORMULA,
                formula=f_val,
            )

        if cell_type is not None:
            return cls(row=row, column=column, value=value, cell_type=cell_type, formula=None)

        if value is None or (isinstance(value, str) and value.strip() == ""):
            return cls(row=row, column=column, value="", cell_type=CellType.EMPTY)

        if isinstance(value, bool):
            return cls(row=row, column=column, value=value, cell_type=CellType.BOOLEAN)

        if isinstance(value, (int, float)):
            return cls(row=row, column=column, value=value, cell_type=CellType.NUMBER)

        # Check numeric string
        if isinstance(value, str):
            v_strip = value.strip()
            if v_strip.lower() in ("true", "false"):
                return cls(row=row, column=column, value=(v_strip.lower() == "true"), cell_type=CellType.BOOLEAN)
            try:
                num_val = int(v_strip) if "." not in v_strip else float(v_strip)
                return cls(row=row, column=column, value=num_val, cell_type=CellType.NUMBER)
            except ValueError:
                pass

        return cls(row=row, column=column, value=str(value), cell_type=CellType.TEXT)


class Worksheet(BaseModel):
    """
    Represents a single tabular sheet containing ordered rows and columns.
    """
    sheet_id: str = Field(default_factory=lambda: f"sheet_{uuid.uuid4().hex[:8]}")
    name: str = Field(default="Sheet1", min_length=1)
    rows: List[List[SpreadsheetCell]] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Worksheet name cannot be empty.")
        return v.strip()

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        if not self.rows:
            return 0
        return max(len(r) for r in self.rows)

    def get_cell(self, row: int, column: int) -> Optional[SpreadsheetCell]:
        """Retrieve cell at given coordinate if exists."""
        if 0 <= row < len(self.rows):
            r_list = self.rows[row]
            if 0 <= column < len(r_list):
                return r_list[column]
        return None

    def set_cell(
        self,
        row: int,
        column: int,
        value: Any,
        cell_type: Optional[CellType] = None,
        formula: Optional[str] = None,
    ) -> SpreadsheetCell:
        """Set or update cell at coordinate, expanding worksheet dimensions as needed."""
        while len(self.rows) <= row:
            self.rows.append([])

        target_row = self.rows[row]
        while len(target_row) <= column:
            col_idx = len(target_row)
            target_row.append(SpreadsheetCell.create(row, col_idx, ""))

        new_cell = SpreadsheetCell.create(row, column, value, cell_type, formula)
        target_row[column] = new_cell
        return new_cell

    def append_row(self, values: List[Any]) -> None:
        """Append a full row of values to the bottom of the worksheet."""
        row_idx = len(self.rows)
        row_cells = [SpreadsheetCell.create(row_idx, col_idx, val) for col_idx, val in enumerate(values)]
        self.rows.append(row_cells)

    def get_raw_values(self) -> List[List[Any]]:
        """Extract a 2D matrix of raw cell values."""
        return [[c.value for c in r] for r in self.rows]


class SpreadsheetMetadata(BaseModel):
    """
    Metadata associated with a workbook.
    """
    author: Optional[str] = "LM-Brain Workforce"
    version: str = "1.0"
    spreadsheet_format: SpreadsheetFormat = SpreadsheetFormat.CSV
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class Workbook(BaseModel):
    """
    Root domain model representing a structured spreadsheet workbook.
    """
    workbook_id: str = Field(default_factory=lambda: f"wb_{uuid.uuid4().hex[:8]}")
    title: str = Field(..., min_length=1)
    worksheets: List[Worksheet] = Field(default_factory=list)
    metadata: SpreadsheetMetadata = Field(default_factory=SpreadsheetMetadata)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Workbook title cannot be empty.")
        return v.strip()

    @property
    def active_sheet(self) -> Worksheet:
        if not self.worksheets:
            sheet = Worksheet(name="Sheet1")
            self.worksheets.append(sheet)
        return self.worksheets[0]

    def get_sheet(self, name_or_idx: Union[str, int]) -> Optional[Worksheet]:
        if isinstance(name_or_idx, int):
            if 0 <= name_or_idx < len(self.worksheets):
                return self.worksheets[name_or_idx]
            return None
        target = str(name_or_idx).strip().lower()
        for s in self.worksheets:
            if s.name.strip().lower() == target:
                return s
        return None

    def add_sheet(self, name: str) -> Worksheet:
        sheet = Worksheet(name=name)
        self.worksheets.append(sheet)
        return sheet


class ColumnSpec(BaseModel):
    """Schema descriptor for a structured tabular column."""
    name: str = Field(..., min_length=1)
    data_type: CellType = Field(default=CellType.TEXT)
    required: bool = Field(default=False)


class SpreadsheetTemplate(BaseModel):
    """
    Reusable deterministic template for creating pre-structured workbooks.
    """
    template_name: str = Field(..., min_length=1)
    description: str = ""
    default_sheet_name: str = "Sheet1"
    columns: List[ColumnSpec] = Field(default_factory=list)
    sample_rows: List[List[Any]] = Field(default_factory=list)

    def instantiate(
        self,
        title: str,
        rows_data: Optional[List[List[Any]]] = None,
    ) -> Workbook:
        """Instantiate a structured Workbook from this template."""
        wb = Workbook(title=title)
        sheet = wb.active_sheet
        sheet.name = self.default_sheet_name

        # Header row from columns
        if self.columns:
            headers = [col.name for col in self.columns]
            sheet.append_row(headers)

        # Body rows
        data = rows_data if rows_data is not None else self.sample_rows
        for row in data:
            sheet.append_row(row)

        return wb
