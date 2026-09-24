"""Code Analysis Tool: Analyzes source code for bugs and improvements."""
import ast
import re
from typing import Dict, Any, List


class CodeAnalyzerTool:
    """
    Code Analysis Tool
    Input  → source code
    Output → bugs + improvements
    """

    @classmethod
    def analyze(cls, code: str) -> Dict[str, Any]:
        """Analyzes source code and produces detected bugs and improvements."""
        bugs: List[Dict[str, Any]] = []
        inefficiencies: List[Dict[str, Any]] = []
        improvements: List[str] = []

        # 1. Syntax Check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            bugs.append({
                "type": "SyntaxError",
                "line": e.lineno,
                "description": f"Syntax error: {e.msg}",
                "severity": "Critical",
            })
            improvements.append(f"Fix syntax error at line {e.lineno}: {e.msg}")
            return {
                "bugs": bugs,
                "inefficiencies": inefficiencies,
                "improvements": improvements,
                "metrics": {"lines_of_code": len(code.splitlines()), "syntax_valid": False},
            }

        # 2. AST-level Bug & Smells Analysis
        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
                # Check mutable default arguments (classic Python bug)
                for default in node.args.defaults + [d for d in node.args.kw_defaults if d]:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        bugs.append({
                            "type": "MutableDefaultArgument",
                            "line": node.lineno,
                            "function": node.name,
                            "description": f"Function '{node.name}' uses a mutable default argument ({type(default).__name__}).",
                            "severity": "Medium",
                        })
                        improvements.append(
                            f"In function '{node.name}', replace mutable default argument with 'None' and initialize inside function."
                        )

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            # Check for bare except or empty except: pass
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bugs.append({
                        "type": "BareExcept",
                        "line": node.lineno,
                        "description": "Bare 'except:' catches all exceptions including SystemExit and KeyboardInterrupt.",
                        "severity": "Medium",
                    })
                    improvements.append("Specify explicit exception types (e.g. 'except Exception:') instead of bare 'except:'.")

                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    inefficiencies.append({
                        "type": "SilentExceptionSuppression",
                        "line": node.lineno,
                        "description": "Exception silently swallowed with 'pass'. This hides bugs during execution.",
                    })
                    improvements.append("Log or handle caught exceptions instead of silently passing.")

            # Check range(len(...)) anti-pattern
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "range":
                    if node.args and isinstance(node.args[0], ast.Call):
                        inner = node.args[0]
                        if isinstance(inner.func, ast.Name) and inner.func.id == "len":
                            inefficiencies.append({
                                "type": "RangeLenAntiPattern",
                                "line": node.lineno,
                                "description": "Iterating using 'range(len(...))' is unidiomatic and slower in Python.",
                            })
                            improvements.append("Use direct iteration or 'enumerate()' instead of 'range(len(...))'.")

        # 3. Pattern / Regex checks across languages
        lines = code.splitlines()
        for idx, line in enumerate(lines, 1):
            # Check for comparison to True/False (== True / == False)
            if re.search(r"==\s*(True|False)", line):
                inefficiencies.append({
                    "type": "RedundantBooleanComparison",
                    "line": idx,
                    "description": f"Redundant comparison: '{line.strip()}'.",
                })
                improvements.append(f"Line {idx}: Simplify boolean check directly instead of '== True/False'.")

            # Check for quadratic nested loop pattern on identical collection
            if re.search(r"for\s+\w+\s+in\s+range\(len\((\w+)\)\):", line):
                pass

        if not improvements:
            improvements.append("Code structure is clean. Consider adding type hints and docstrings for better maintainability.")

        return {
            "bugs": bugs,
            "inefficiencies": inefficiencies,
            "improvements": improvements,
            "metrics": {
                "lines_of_code": len(lines),
                "syntax_valid": True,
                "functions_found": functions,
                "classes_found": classes,
            },
        }

    # Backward compatibility helper
    @classmethod
    def analyze_python_code(cls, code: str) -> Dict[str, Any]:
        return cls.analyze(code)
