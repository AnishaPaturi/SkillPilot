"""Code Explanation Tool: Explains source code in clear, understandable language."""
import ast
import re
from typing import Dict, Any, List


class CodeExplainerTool:
    """
    Code Explanation Tool
    Input  → code
    Output → explanation (High-level explanation, Step-by-step execution, Important concepts, Example)
    """

    @classmethod
    def explain(cls, code: str) -> Dict[str, Any]:
        """Generates a structured, clear explanation of the provided source code."""
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        line_count = len(lines)

        # Parse AST to extract structured metadata
        functions = []
        classes = []
        has_loops = False
        has_recursion = False
        has_async = False
        has_try_except = False

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    if isinstance(node, ast.AsyncFunctionDef):
                        has_async = True
                    # Check recursion
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                            if subnode.func.id == node.name:
                                has_recursion = True
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.For, ast.While)):
                    has_loops = True
                elif isinstance(node, ast.Try):
                    has_try_except = True
        except Exception:
            pass

        # 1. High-Level Explanation
        summary_parts = []
        if classes:
            summary_parts.append(f"defines class `{classes[0]}` to encapsulate related state and behaviors")
        if functions:
            summary_parts.append(f"implements logic via function(s) `{', '.join(functions)}`")
        if has_recursion:
            summary_parts.append("uses a recursive divide-and-conquer strategy")
        elif has_loops:
            summary_parts.append("processes items iteratively through loops")
        if has_async:
            summary_parts.append("operates asynchronously using coroutines")

        action_summary = " and ".join(summary_parts) if summary_parts else "processes input data to compute results"
        high_level = f"This code snippet ({line_count} lines) {action_summary}."

        # 2. Step-by-step execution
        step_by_step: List[str] = []
        raw_lines = code.splitlines()
        step_num = 1
        for idx, line in enumerate(raw_lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            explanation = None
            if re.match(r"^def\s+(\w+)\((.*?)\):", stripped):
                fn_name = re.match(r"^def\s+(\w+)", stripped).group(1)
                explanation = f"Declares function `{fn_name}`, receiving incoming parameters."
            elif re.match(r"^class\s+(\w+)", stripped):
                cls_name = re.match(r"^class\s+(\w+)", stripped).group(1)
                explanation = f"Defines object blueprint `{cls_name}`."
            elif re.match(r"^(for|while)\s+", stripped):
                explanation = f"Begins loop iteration: `{stripped}`."
            elif re.match(r"^if\s+", stripped):
                explanation = f"Evaluates conditional branch condition: `{stripped}`."
            elif re.match(r"^return\s+", stripped):
                explanation = f"Returns computation result back to caller: `{stripped}`."
            elif "=" in stripped and not stripped.startswith("=="):
                explanation = f"Assigns or computes variable state: `{stripped}`."

            if explanation and step_num <= 8:
                step_by_step.append(f"**Step {step_num} (Line {idx}):** {explanation}")
                step_num += 1

        if not step_by_step:
            step_by_step = [
                "1. Initializes input parameters and execution context.",
                "2. Executes main algorithm logic sequentially.",
                "3. Produces and returns output to caller.",
            ]

        # 3. Important Concepts
        concepts: List[str] = []
        if has_recursion:
            concepts.append("**Recursion**: Function calls itself with a reduced subproblem until reaching a base condition.")
        if has_async:
            concepts.append("**Asynchronous I/O**: Uses non-blocking coroutines for concurrency.")
        if has_try_except:
            concepts.append("**Defensive Error Handling**: Uses structured try/except blocks to catch runtime exceptions.")
        if classes:
            concepts.append("**Object-Oriented Programming (OOP)**: Encapsulates state and methods inside classes.")
        if has_loops:
            concepts.append("**Iteration & Control Flow**: Sequentially traverses sequences.")
        if not concepts:
            concepts.append("**Modular Decomposition**: Breaks procedural logic into reusable components.")

        # 4. Example Where Useful
        target_fn = functions[0] if functions else "compute"
        example = f"""```python
# Practical usage example
result = {target_fn}(...)
print("Execution output:", result)
```"""

        # Formatted Markdown
        markdown_explanation = f"""## Code Explanation

### 1. High-Level Explanation
{high_level}

### 2. Step-by-Step Execution
{chr(10).join(step_by_step)}

### 3. Important Concepts
{chr(10).join(f"- {c}" for c in concepts)}

### 4. Example Where Useful
{example}
"""

        return {
            "high_level_explanation": high_level,
            "step_by_step_execution": step_by_step,
            "important_concepts": concepts,
            "example": example,
            "markdown_explanation": markdown_explanation,
        }
