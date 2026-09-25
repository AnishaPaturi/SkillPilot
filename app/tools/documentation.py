"""Documentation Tool: Generates technical documentation from project descriptions or code."""
import ast
import re
from typing import Dict, Any, List


class DocumentationTool:
    """
    Documentation Tool
    Input  → project/code
    Output → documentation (Overview, Features, Architecture, Installation, Usage, Config, Examples)
    """

    @classmethod
    def generate(cls, project_or_code: str) -> Dict[str, Any]:
        """Generates comprehensive documentation matching the 7 specification sections."""
        api_surface = cls.extract_api_surface(project_or_code)
        classes = api_surface.get("classes", [])
        functions = api_surface.get("functions", [])
        endpoints = api_surface.get("endpoints", [])

        # Heuristic project name derivation
        title = "Project Documentation"
        if classes:
            title = f"{classes[0]['name']} API Documentation"
        elif functions:
            title = f"{functions[0]['name']} Module Documentation"

        # Check for prior security analysis findings in the context
        security_findings: List[Dict[str, str]] = []
        if "Security Vulnerability Report" in project_or_code or "vulnerability" in project_or_code.lower():
            vuln_blocks = re.findall(
                r"###\s*1\.\s*Vulnerability:\s*([^\n]+).*?"
                r"###\s*2\.\s*Severity:\s*([^\n]+).*?"
                r"###\s*3\.\s*Explanation:\s*([^\n]+).*?"
                r"###\s*4\.\s*Potential Impact:\s*([^\n]+).*?"
                r"###\s*5\.\s*Recommended Mitigation:\s*([^\n\r]+)",
                project_or_code,
                re.DOTALL,
            )
            for v_name, sev, expl, impact, mitig in vuln_blocks:
                security_findings.append({
                    "vulnerability": v_name.strip(),
                    "severity": sev.strip(),
                    "explanation": expl.strip(),
                    "potential_impact": impact.strip(),
                    "mitigation": mitig.strip(),
                })

        # 1. Overview
        overview = (
            f"Technical documentation generated for `{title}`. "
            f"Provides interfaces and module capabilities across "
            f"{len(classes)} classes and {len(functions)} functions."
        )
        if security_findings:
            overview += (
                f"\n\n**Security Notice:** Static security analysis identified "
                f"{len(security_findings)} potential vulnerability/ies in this API. "
                f"Detailed explanations and recommended mitigations are documented below."
            )

        # 2. Features
        features: List[str] = []
        for cls_item in classes:
            features.append(f"**{cls_item['name']}**: {cls_item['docstring'][:100]}")
        for fn_item in functions:
            features.append(f"**{fn_item['name']}({', '.join(fn_item['arguments'])})**: {fn_item['docstring'][:100]}")
        for ep in endpoints:
            features.append(f"**Endpoint [{ep['method']}] `{ep['path']}`**: {ep['name']}")

        if security_findings:
            features.append("Security Vulnerability Assessment & Defensive Mitigation Guidelines")

        if not features:
            features = [
                "Modular, decoupled architecture",
                "Automated parameter validation and error handling",
                "Extensible interface for custom adapters",
            ]

        # 3. Architecture
        arch_lines = [
            "The system is organized into modular layers with clear separation of concerns:"
        ]
        if classes:
            arch_lines.append(f"- **Core Components**: {', '.join(c['name'] for c in classes)}")
        if functions:
            arch_lines.append(f"- **Utility Functions**: {', '.join(f['name'] for f in functions)}")
        architecture = "\n".join(arch_lines)

        # 4. Installation
        installation = """```bash
# Clone the repository
git clone <repository_url>
cd <repository_folder>

# Install dependencies
pip install -r requirements.txt
```"""

        # 5. Usage
        usage_snippets = []
        if classes:
            c = classes[0]
            usage_snippets.append(f"from module import {c['name']}\n\ninstance = {c['name']}()")
        elif functions:
            f = functions[0]
            args_str = ", ".join(f['arguments'])
            usage_snippets.append(f"from module import {f['name']}\n\nresult = {f['name']}({args_str})")
        else:
            usage_snippets.append("# Import and initialize module\nimport project\n\nproject.run()")

        usage = f"```python\n{chr(10).join(usage_snippets)}\n```"

        # 6. Configuration
        config_lines = [
            "```ini",
            "# Environment settings (.env)",
            "DEBUG=False",
            "PORT=8000",
            "API_KEY=your_api_key_here",
            "```",
        ]
        if security_findings:
            config_lines.append("\n### Identified Vulnerabilities & Security Mitigations:")
            for sf in security_findings:
                config_lines.append(f"- **{sf['vulnerability']}** (Severity: {sf['severity']})")
                config_lines.append(f"  - **Explanation:** {sf['explanation']}")
                config_lines.append(f"  - **Potential Impact:** {sf['potential_impact']}")
                config_lines.append(f"  - **Recommended Mitigation:** {sf['mitigation']}")
        configuration = "\n".join(config_lines)

        # 7. Examples
        examples = f"""```python
# Complete execution example
{chr(10).join(usage_snippets)}
print("Success:", result if 'result' in locals() else "Executed successfully")
```"""

        # Compose Complete Markdown Document
        markdown_doc = f"""# {title}

## 1. Overview
{overview}

## 2. Features
{chr(10).join(f"- {feat}" for feat in features)}

## 3. Architecture
{architecture}

## 4. Installation
{installation}

## 5. Usage
{usage}

## 6. Configuration
{configuration}

## 7. Examples
{examples}
"""

        return {
            "title": title,
            "overview": overview,
            "features": features,
            "architecture": architecture,
            "installation": installation,
            "usage": usage,
            "configuration": configuration,
            "examples": examples,
            "markdown_doc": markdown_doc,
        }

    @staticmethod
    def extract_api_surface(code: str) -> Dict[str, Any]:
        """Extracts functions, classes, and HTTP route endpoints from code."""
        api_surface: Dict[str, Any] = {"classes": [], "functions": [], "endpoints": []}
        source_code = code
        if "# ========================================================" in code:
            source_code = code.split("# ========================================================")[0].strip()

        try:
            tree = ast.parse(source_code)
        except Exception:
            # Fallback regex search if not valid Python AST
            endpoints = re.findall(r'@\w+\.(get|post|put|delete)\(["\']([^"\']+)["\']\)', source_code, re.IGNORECASE)
            for method, path in endpoints:
                api_surface["endpoints"].append({"method": method.upper(), "path": path, "name": "API Route"})
            return api_surface

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node) or "No docstring provided."
                args = [arg.arg for arg in node.args.args]
                api_surface["functions"].append({
                    "name": node.name,
                    "arguments": args,
                    "docstring": doc,
                })

                # Check route decorators (FastAPI/Flask)
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        method = decorator.func.attr
                        if method in {"get", "post", "put", "delete", "patch"} and decorator.args:
                            if isinstance(decorator.args[0], ast.Constant):
                                api_surface["endpoints"].append({
                                    "method": method.upper(),
                                    "path": str(decorator.args[0].value),
                                    "name": node.name,
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
