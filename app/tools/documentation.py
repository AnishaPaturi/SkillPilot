"""Tool for extracting code structures and docstrings to aid documentation generation."""
import ast
from typing import Dict, Any, List


class DocumentationTool:
    """Extracts signatures and docstrings from Python modules."""

    @staticmethod
    def extract_api_surface(code: str) -> Dict[str, Any]:
        """Extracts modules, classes, and function signatures with their docstrings."""
        api_surface: Dict[str, Any] = {"classes": [], "functions": []}
        try:
            tree = ast.parse(code)
        except Exception:
            return api_surface

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or "No docstring provided."
                args = [arg.arg for arg in node.args.args]
                api_surface["functions"].append({
                    "name": node.name,
                    "arguments": args,
                    "docstring": doc,
                })
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or "No docstring provided."
                methods = [
                    m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                api_surface["classes"].append({
                    "name": node.name,
                    "methods": methods,
                    "docstring": doc,
                })

        return api_surface
