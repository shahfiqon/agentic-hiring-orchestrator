"""Graph module for hiring workflow orchestration.

The actual implementation is in ../graph.py (sibling file to this directory).
This __init__.py re-exports the main function for convenience.
"""

import importlib.util
from pathlib import Path

# Load the graph.py module from the parent directory
_graph_py_path = Path(__file__).parent.parent / "graph.py"
_spec = importlib.util.spec_from_file_location("_graph_module", _graph_py_path)
_graph_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_graph_module)

# Re-export the main function
run_hiring_workflow = _graph_module.run_hiring_workflow

__all__ = ["run_hiring_workflow"]
