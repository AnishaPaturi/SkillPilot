"""Tool for scanning code for common security anti-patterns."""
import re
from typing import List, Dict, Any


class SecurityAnalyzerTool:
    """Scans code for common security vulnerabilities (secrets, dangerous functions, injections)."""

    PATTERNS = [
        ("HARDCODED_SECRET", r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "High", "Hardcoded credentials or API tokens detected."),
        ("DANGEROUS_EVAL", r"\b(eval|exec)\s*\(", "Critical", "Dynamic code execution via eval/exec allows arbitrary code execution."),
        ("COMMAND_INJECTION", r"subprocess\.(Popen|run|call)\(.*shell\s*=\s*True", "Critical", "Subprocess execution with shell=True invites command injection."),
        ("SQL_INJECTION", r"(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*?\s*(\+|%|\.format|\$)", "High", "Potential SQL query concatenation without parameterized queries."),
        ("INSECURE_DESERIALIZATION", r"pickle\.loads?\s*\(", "High", "Pickle deserialization from untrusted input enables remote code execution."),
    ]

    @classmethod
    def scan_security_issues(cls, code: str) -> List[Dict[str, Any]]:
        """Finds regex-based vulnerability matches in source code."""
        findings = []
        for issue_type, pattern, severity, explanation in cls.PATTERNS:
            matches = list(re.finditer(pattern, code))
            if matches:
                for match in matches:
                    findings.append({
                        "issue_type": issue_type,
                        "severity": severity,
                        "explanation": explanation,
                        "matched_text": match.group(0),
                    })
        return findings
