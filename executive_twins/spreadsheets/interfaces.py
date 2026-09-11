from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from executive_twins.spreadsheets.models import (
    SpreadsheetMetadata,
    Workbook,
    Worksheet,
)


class ISpreadsheetBuilder(ABC):
    """
    Provider-independent Spreadsheet Builder interface.
    Provides fluent, declarative construction of typed Workbook and Worksheet objects.
    """

    @abstractmethod
    def set_title(self, title: str) -> "ISpreadsheetBuilder":
        """Set workbook title."""
        pass

    @abstractmethod
    def set_metadata(self, metadata: SpreadsheetMetadata) -> "ISpreadsheetBuilder":
        """Set workbook metadata."""
        pass

    @abstractmethod
    def add_worksheet(self, name: str) -> "ISpreadsheetBuilder":
        """Add and switch focus to a new worksheet."""
        pass

    @abstractmethod
    def set_active_worksheet(self, name_or_idx: Union[str, int]) -> "ISpreadsheetBuilder":
        """Switch active worksheet scope."""
        pass

    @abstractmethod
    def add_row(self, values: List[Any]) -> "ISpreadsheetBuilder":
        """Append row to current active worksheet."""
        pass

    @abstractmethod
    def set_cell(
        self,
        row: int,
        column: int,
        value: Any,
        formula: Optional[str] = None,
    ) -> "ISpreadsheetBuilder":
        """Set cell at coordinate in current active worksheet."""
        pass

    @abstractmethod
    def build(self) -> Workbook:
        """Validate and return assembled Workbook instance."""
        pass

    @abstractmethod
    def reset(self) -> "ISpreadsheetBuilder":
        """Clear internal builder state for reuse."""
        pass


class ISpreadsheetParser(ABC):
    """
    Provider-independent Spreadsheet Parser interface.
    Converts raw tabular text strings (CSV, TSV) into structured Workbook models.
    """

    @abstractmethod
    def parse(
        self,
        content: str,
        delimiter: str = ",",
        sheet_name: str = "Sheet1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Workbook:
        """Parse tabular string content into a Workbook instance."""
        pass


class ISpreadsheetRenderer(ABC):
    """
    Provider-independent Spreadsheet Renderer interface.
    Transforms structured Workbook models into target tabular string representations (CSV / TSV).
    """

    @abstractmethod
    def render(
        self,
        workbook: Workbook,
        sheet_name_or_idx: Optional[Union[str, int]] = None,
        delimiter: str = ",",
    ) -> str:
        """Render a Workbook sheet into tabular string format."""
        pass


class ISpreadsheetSpecialist(ABC):
    """
    Spreadsheet Specialist Worker interface.
    Defines specialist domain contracts for synthesizing, editing, and validating tabular data.
    """

    @abstractmethod
    def synthesize_spreadsheet(
        self,
        title: str,
        topic: str,
        columns: Optional[List[str]] = None,
        rows: Optional[List[List[Any]]] = None,
    ) -> Workbook:
        """Synthesize a structured workbook from tabular intent/spec."""
        pass

    @abstractmethod
    def edit_spreadsheet(
        self,
        workbook: Workbook,
        instructions: str,
        edits: Dict[str, Any],
    ) -> Workbook:
        """Apply structured modifications, cell updates, or row/column mutations to an existing workbook."""
        pass

    @abstractmethod
    def validate_spreadsheet(
        self,
        workbook: Workbook,
    ) -> Dict[str, Any]:
        """Validate structural integrity, dimensions, formulas, and schema compliance of a workbook."""
        pass
