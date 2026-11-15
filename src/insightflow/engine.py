import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

from .database import DatabaseManager, ExecutionResult
from .security import SQLSecurityValidator
from .schema import SchemaInspector

@dataclass
class QuerySynthesisResult:
    prompt: str
    generated_sql: str
    is_safe: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    duration_ms: float
    query_plan: List[str]
    explanation: str

class QueryEngine:
    """Translates natural language questions to validated relational SQL queries."""

    def __init__(self, db_manager: DatabaseManager, security_validator: Optional[SQLSecurityValidator] = None):
        self.db = db_manager
        self.security = security_validator or SQLSecurityValidator()

        # Semantic analytical intent mappings
        self._intent_patterns = [
            (
                r"\b(top|best|highest|leading)\s+(product|item|sku|offering)s?\b",
                "SELECT p.product_name, p.category, SUM(t.quantity) AS total_units_sold, ROUND(SUM(t.total_amount), 2) AS total_revenue "
                "FROM transactions t JOIN products p ON t.product_id = p.product_id "
                "GROUP BY p.product_id ORDER BY total_revenue DESC LIMIT 5",
                "Aggregated top-performing products ranked by gross transactional revenue."
            ),
            (
                r"\b(region|geography|territory|location)s?\b",
                "SELECT a.region, COUNT(DISTINCT a.account_id) AS active_accounts, COUNT(t.transaction_id) AS transaction_count, ROUND(SUM(t.total_amount), 2) AS regional_revenue "
                "FROM accounts a JOIN transactions t ON a.account_id = t.account_id "
                "GROUP BY a.region ORDER BY regional_revenue DESC",
                "Segmented gross revenues and transaction volume across geographic sales territories."
            ),
            (
                r"\b(top|biggest|leading)\s+(client|account|customer|company|spender)s?\b",
                "SELECT a.company_name, a.industry, a.region, COUNT(t.transaction_id) AS orders_placed, ROUND(SUM(t.total_amount), 2) AS lifetime_spend "
                "FROM accounts a JOIN transactions t ON a.account_id = t.account_id "
                "GROUP BY a.account_id ORDER BY lifetime_spend DESC LIMIT 5",
                "Calculated top corporate accounts ranked by cumulative lifetime billing spend."
            ),
            (
                r"\b(monthly|trend|timeline|month|date)\b",
                "SELECT SUBSTR(transacted_at, 1, 7) AS billing_month, COUNT(transaction_id) AS transaction_volume, ROUND(SUM(total_amount), 2) AS monthly_revenue "
                "FROM transactions GROUP BY billing_month ORDER BY billing_month ASC",
                "Aggregated monthly transaction frequencies and revenue growth timeline."
            ),
            (
                r"\b(category|categories|software|infrastructure|services)\b",
                "SELECT p.category, COUNT(DISTINCT p.product_id) AS product_count, ROUND(SUM(t.total_amount), 2) AS category_revenue "
                "FROM products p JOIN transactions t ON p.product_id = t.product_id "
                "GROUP BY p.category ORDER BY category_revenue DESC",
                "Classified revenue distribution across high-level product categories."
            )
        ]

    def translate_to_sql(self, prompt: str) -> Tuple[str, str]:
        for pattern, sql, explanation in self._intent_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return sql, explanation

        return (
            "SELECT p.product_name, p.category, ROUND(SUM(t.total_amount), 2) AS total_revenue "
            "FROM transactions t JOIN products p ON t.product_id = p.product_id "
            "GROUP BY p.product_id ORDER BY total_revenue DESC LIMIT 5",
            "General fallback: Identified top revenue-generating offerings."
        )

    def execute_prompt(self, prompt: str, raw_sql: Optional[str] = None) -> QuerySynthesisResult:
        if raw_sql and raw_sql.strip():
            candidate_sql = raw_sql.strip()
            explanation = "Executed custom SQL payload."
        else:
            candidate_sql, explanation = self.translate_to_sql(prompt)

        check = self.security.validate_and_sanitize(candidate_sql)
        if not check.is_safe:
            return QuerySynthesisResult(
                prompt=prompt,
                generated_sql=candidate_sql,
                is_safe=False,
                columns=[],
                rows=[],
                row_count=0,
                duration_ms=0.0,
                query_plan=[],
                explanation=f"Security Rejection: {check.violation_reason}"
            )

        exec_res = self.db.execute_query(check.sanitized_sql)

        return QuerySynthesisResult(
            prompt=prompt,
            generated_sql=check.sanitized_sql,
            is_safe=True,
            columns=exec_res.columns,
            rows=exec_res.rows,
            row_count=exec_res.row_count,
            duration_ms=exec_res.duration_ms,
            query_plan=exec_res.query_plan,
            explanation=explanation
        )
