"""
Pytest configuration for specialist-agent tests.

Adds the specialist-agent project directory to sys.path so that
specialist_agent is importable as a top-level package.
"""

from __future__ import annotations

import sys
import os

# The specialist-agent/ directory contains the specialist_agent/ package
# Add it to sys.path so tests can import: from specialist_agent.core.agent import ...
specialist_agent_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if specialist_agent_project_root not in sys.path:
    sys.path.insert(0, specialist_agent_project_root)
