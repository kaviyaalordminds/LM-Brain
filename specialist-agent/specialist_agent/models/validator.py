"""
Specialist Agent — Structured Output Validator

Ensures model outputs conform to expected schema and invariants before execution.
Rejects malformed outputs with INVALID_OUTPUT error code.
Never guesses what the model intended.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class StructuredOutputValidator:
    """
    Validates model text/JSON responses against expected keys and schemas.
    """

    @staticmethod
    def validate_json(
        raw_text: str,
        required_keys: Optional[list[str]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempt to parse raw model text as JSON and check for required keys.

        Returns:
            (is_valid, parsed_dict, error_message)
        """
        if not raw_text or not raw_text.strip():
            return False, None, "INVALID_OUTPUT: Model returned empty response"

        # Try extracting JSON if wrapped in markdown code blocks
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed = json.loads(clean_text)
            if not isinstance(parsed, dict):
                return False, None, f"INVALID_OUTPUT: Expected JSON object, got {type(parsed).__name__}"

            if required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    return False, parsed, f"INVALID_OUTPUT: Response missing required keys: {missing}"

            return True, parsed, None
        except json.JSONDecodeError as exc:
            return False, None, f"INVALID_OUTPUT: Malformed JSON response: {str(exc)}"
