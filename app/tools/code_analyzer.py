"""Tool for static code analysis, syntax checking, and metrics."""
import ast
from typing import Dict, Any, List


class CodeAnalyzerTool:
    """Performs deterministic static analysis on code snippets."""

    @staticmethod
    def analyze_python_code(code: str) -> Dict[str, Any]:
        """Analyzes Python code for syntax validity, structures, and potential smells."""
        result: Dict[str, Any] = {
            "syntax_valid": True,
            "syntax_error": None,
            "functions": [],
            "classes": [],
            "imports": [],
            "lines_of_code": len(code.splitlines()),
        }

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["syntax_valid"] = False
            result["syntax_error"] = f"Line {e.lineno}: {e.msg}"
            return result

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                result["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                result["classes"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                result["imports"].append(node.module or "")

        return result
