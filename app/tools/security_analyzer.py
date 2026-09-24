"""Security Analysis Tool: Scans source code and configurations for vulnerabilities and mitigations."""
import re
from typing import List, Dict, Any


class SecurityAnalyzerTool:
    """
    Security Analysis Tool
    Input  → source/config
    Output → vulnerabilities + mitigations
    """

    PATTERNS = [
        (
            "HARDCODED_SECRET",
            r"(?i)(?:api[_-]?key|secret|token|password|passwd|auth|access[_-]?key)[a-z0-9_]*\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]",
            "High",
            "Hardcoded credential or API secret token detected in plain text.",
            "Credentials exposed in source control can be compromised leading to unauthorized access.",
            "Move sensitive credentials to secure environment variables or a secrets manager (e.g., Vault, AWS Secrets Manager).",
        ),
        (
            "DANGEROUS_EVAL",
            r"\b(eval|exec)\s*\(",
            "Critical",
            "Dynamic code execution via eval/exec allows arbitrary code execution from untrusted inputs.",
            "Remote attackers can execute arbitrary system commands or take over application process.",
            "Avoid eval/exec entirely. Use safe deserialization (e.g., json.loads, ast.literal_eval) or explicit parser logic.",
        ),
        (
            "COMMAND_INJECTION",
            r"(subprocess\.(Popen|run|call|check_output)\(.*shell\s*=\s*True|os\.system\(|os\.popen\()",
            "Critical",
            "Invoking shell execution with untrusted parameters invites command injection vulnerabilities.",
            "Attackers can inject shell metacharacters (; & | `) to execute arbitrary commands with host privileges.",
            "Pass arguments as a list with shell=False (e.g., subprocess.run(['cmd', arg])) to prevent shell interpolation.",
        ),
        (
            "SQL_INJECTION",
            r"(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*?\s*(\+|%|\.format\(|\$[A-Za-z0-9_]+)",
            "High",
            "Dynamic SQL query construction detected using string concatenation or formatting.",
            "Attackers can manipulate database queries to bypass authentication, read or destroy database data.",
            "Use parameterized queries, prepared statements, or an ORM (e.g., SQLAlchemy, Hibernate) with bound parameters.",
        ),
        (
            "INSECURE_DESERIALIZATION",
            r"(pickle\.loads?\s*\(|yaml\.load\s*\([^,)]+\))",
            "High",
            "Insecure deserialization of untrusted payloads using pickle or unsafe yaml.load.",
            "Can lead to arbitrary object instantiation and Remote Code Execution (RCE).",
            "Use safe serialization formats like JSON, or yaml.safe_load() when parsing YAML.",
        ),
        (
            "INSECURE_CONFIG_DEBUG",
            r"(?i)(DEBUG\s*=\s*True|ENV\s*=\s*['\"]development['\"])",
            "Medium",
            "Debug mode enabled in configuration.",
            "Verbose debug stack traces expose internal environment details and sensitive state.",
            "Ensure DEBUG is disabled (False) in staging and production environments.",
        ),
        (
            "PERMISSIVE_CORS",
            r"(?i)(allow_origins\s*=\s*\[['\"]\s*\*['\"]\s*\]|Access-Control-Allow-Origin:\s*\*)",
            "Medium",
            "Wildcard permissive CORS policy detected.",
            "Enables malicious origins to make authenticated cross-origin requests.",
            "Restrict allowed origins to trusted and validated domains.",
        ),
    ]

    @classmethod
    def analyze(cls, source_or_config: str) -> Dict[str, Any]:
        """
        Scans source code or configuration text.
        Returns:
            {
                "vulnerabilities": [...],
                "mitigations": [...]
            }
        """
        vulnerabilities: List[Dict[str, Any]] = []
        mitigations: List[str] = []

        lines = source_or_config.splitlines()

        for (
            vuln_id,
            pattern,
            severity,
            explanation,
            impact,
            mitigation_text,
        ) in cls.PATTERNS:
            for idx, line in enumerate(lines, 1):
                match = re.search(pattern, line)
                if match:
                    # Obfuscate secret in matched text if needed
                    matched_snippet = line.strip()
                    if vuln_id == "HARDCODED_SECRET" and len(matched_snippet) > 40:
                        matched_snippet = matched_snippet[:35] + "..."

                    vulnerabilities.append({
                        "vulnerability": vuln_id.replace("_", " ").title(),
                        "severity": severity,
                        "line": idx,
                        "matched_content": matched_snippet,
                        "explanation": explanation,
                        "potential_impact": impact,
                        "recommended_mitigation": mitigation_text,
                    })

                    if mitigation_text not in mitigations:
                        mitigations.append(mitigation_text)

        # Determine overall severity level
        severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        max_severity = "Clean"
        if vulnerabilities:
            max_severity = max(
                (v["severity"] for v in vulnerabilities),
                key=lambda s: severity_order.get(s, 0),
            )

        return {
            "vulnerabilities": vulnerabilities,
            "mitigations": mitigations,
            "total_vulnerabilities": len(vulnerabilities),
            "overall_severity": max_severity,
        }

    # Backward compatibility helper
    @classmethod
    def scan_security_issues(cls, code: str) -> List[Dict[str, Any]]:
        result = cls.analyze(code)
        return result["vulnerabilities"]
