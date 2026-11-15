import re
from dataclasses import dataclass
from typing import Optional, Set

FORBIDDEN_KEYWORDS: Set[str] = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "ATTACH", "DETACH", "PRAGMA", "EXEC",
    "VACUUM", "REINDEX", "GRANT", "REVOKE"
}

@dataclass
class SecurityCheckResult:
    is_safe: bool
    sanitized_sql: str
    violation_reason: Optional[str] = None

class SQLSecurityValidator:
    """Enforces strict analytical read-only query policy and anti-injection guards."""

    def __init__(self, max_limit: int = 100):
        self.max_limit = max_limit

    def validate_and_sanitize(self, sql_query: str) -> SecurityCheckResult:
        trimmed = sql_query.strip()
        if not trimmed:
            return SecurityCheckResult(is_safe=False, sanitized_sql="", violation_reason="Query string is empty.")

        # Disallow statement chaining with semicolons
        statements = [s.strip() for s in trimmed.split(";") if s.strip()]
        if len(statements) > 1:
            return SecurityCheckResult(
                is_safe=False,
                sanitized_sql="",
                violation_reason="Multiple SQL statements in a single execution payload are prohibited."
            )

        single_query = statements[0]

        # Verify query begins with SELECT or WITH (Common Table Expression)
        if not re.match(r"^(SELECT|WITH)\b", single_query, re.IGNORECASE):
            return SecurityCheckResult(
                is_safe=False,
                sanitized_sql="",
                violation_reason="Only read-only SELECT and WITH queries are authorized."
            )

        # Check for forbidden mutations
        upper_q = single_query.upper()
        for kw in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", upper_q):
                return SecurityCheckResult(
                    is_safe=False,
                    sanitized_sql="",
                    violation_reason=f"Forbidden keyword '{kw}' detected. Mutations are blocked."
                )

        # Enforce or inject LIMIT clause to prevent out-of-memory table dumps
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", single_query, re.IGNORECASE)
        if limit_match:
            existing_limit = int(limit_match.group(1))
            if existing_limit > self.max_limit:
                # Replace with max limit
                sanitized = re.sub(
                    r"\bLIMIT\s+\d+\b",
                    f"LIMIT {self.max_limit}",
                    single_query,
                    flags=re.IGNORECASE
                )
            else:
                sanitized = single_query
        else:
            sanitized = f"{single_query} LIMIT {self.max_limit}"

        return SecurityCheckResult(is_safe=True, sanitized_sql=sanitized)
