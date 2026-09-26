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

        # Check if code is Java before reporting Python syntax failure
        is_java = any(k in code for k in [
            "public class", "private ", "protected ", "public static void",
            "System.out", "ArrayList<", "List<", "Map<", "String[]", "package "
        ])

        if is_java:
            return cls._analyze_java(code)

        # 1. Python Syntax Check
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

    @classmethod
    def _analyze_java(cls, code: str) -> Dict[str, Any]:
        """Analyzes Java source code for common bugs, concurrency risks, and code smells."""
        bugs: List[Dict[str, Any]] = []
        inefficiencies: List[Dict[str, Any]] = []
        improvements: List[str] = []

        lines = code.splitlines()
        has_arraylist = False
        has_synchronization = False
        class_names = []

        for idx, line in enumerate(lines, 1):
            clean_l = line.strip()

            # Detect class definition
            class_match = re.search(r"class\s+(\w+)", clean_l)
            if class_match:
                class_names.append(class_match.group(1))

            # Concurrency / Thread safety check
            if "ArrayList" in clean_l:
                has_arraylist = True
            if "synchronized" in clean_l or "Concurrent" in clean_l or "CopyOnWrite" in clean_l:
                has_synchronization = True

            # String equality check (== instead of .equals)
            if re.search(r'\w+\s*==\s*".*"', clean_l) or re.search(r'".*"\s*==\s*\w+', clean_l):
                bugs.append({
                    "type": "StringReferenceComparison",
                    "line": idx,
                    "description": "String comparison performed with '==' instead of '.equals()'. This compares references rather than values.",
                    "severity": "High",
                })
                improvements.append(f"Line {idx}: Replace '==' with '.equals()' for String comparison.")

            # Missing null check on add/put
            if re.search(r"\b(add|put)\s*\(\s*(\w+)\s*\)", clean_l):
                arg = re.search(r"\b(add|put)\s*\(\s*(\w+)\s*\)", clean_l).group(2)
                if arg not in ["null", "true", "false"] and not arg.isdigit():
                    inefficiencies.append({
                        "type": "PotentialNullPointerException",
                        "line": idx,
                        "description": f"Adding '{arg}' to collection without null validation check.",
                    })
                    improvements.append(f"Line {idx}: Validate '{arg} != null' before inserting into collection.")

            # Empty catch block
            if re.search(r"catch\s*\([^)]+\)\s*\{\s*\}", clean_l):
                bugs.append({
                    "type": "EmptyCatchBlock",
                    "line": idx,
                    "description": "Exception caught and completely swallowed with empty catch block.",
                    "severity": "Medium",
                })
                improvements.append(f"Line {idx}: Log the exception or rethrow properly.")

        if has_arraylist and not has_synchronization:
            bugs.append({
                "type": "ThreadSafetyHazard",
                "line": 1,
                "description": "ArrayList is not thread-safe. Concurrent modifications by multiple threads will lead to race conditions or ConcurrentModificationException.",
                "severity": "Medium",
            })
            improvements.append("Use a thread-safe collection (e.g. Collections.synchronizedList or CopyOnWriteArrayList) if accessed concurrently.")

        if not improvements:
            improvements.append("Java structure is clean. Consider adding JavaDoc comments and defensive copy getters.")

        return {
            "bugs": bugs,
            "inefficiencies": inefficiencies,
            "improvements": improvements,
            "metrics": {
                "lines_of_code": len(lines),
                "syntax_valid": True,
                "classes_found": class_names,
                "language": "java",
            },
        }

    # Backward compatibility helper
    @classmethod
    def analyze_python_code(cls, code: str) -> Dict[str, Any]:
        return cls.analyze(code)

