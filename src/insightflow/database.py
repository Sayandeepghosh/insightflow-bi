import sqlite3
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ExecutionResult:
    sql: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    duration_ms: float
    query_plan: List[str]

class DatabaseManager:
    """Manages SQLite connections, schema seeding, and telemetry execution."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_connection()

    def _init_connection(self):
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._init_connection()
        return self._conn

    def seed_default_tables(self):
        """Initializes normalized business schema and transactional records."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY,
            company_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            region TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            account_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            transacted_at TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """)

        # Insert seed records if empty
        cursor.execute("SELECT COUNT(*) FROM products;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO accounts (account_id, company_name, industry, region, created_at) VALUES (?, ?, ?, ?, ?)
            """, [
                (1, "Aetherius Cloud Systems", "Fintech", "EMEA", "2024-01-10"),
                (2, "Veritas Biotech Labs", "Healthcare", "North America", "2024-01-22"),
                (3, "Hyperion Dynamics", "Autonomous Systems", "APAC", "2024-02-14"),
                (4, "Solaria Grid Technologies", "Energy", "North America", "2024-03-01"),
                (5, "Meridian Retail Platform", "E-Commerce", "EMEA", "2024-03-18")
            ])

            cursor.executemany("""
            INSERT INTO products (product_id, sku, product_name, category, unit_price) VALUES (?, ?, ?, ?, ?)
            """, [
                (1, "AI-AGENT-ENT", "Autonomous Agent Enterprise Node", "Software", 850.0),
                (2, "RAG-VECTOR-10M", "Vector Embedding Cluster (10M Vectors)", "Infrastructure", 320.0),
                (3, "FASTAPI-SEC-GW", "API Security Gateway Proxy", "Software", 210.0),
                (4, "DEDICATED-H100", "Dedicated GPU Compute Node", "Infrastructure", 1850.0),
                (5, "SUPPORT-SLA-GOLD", "24/7 SLA Engineering Retainer", "Services", 600.0)
            ])

            cursor.executemany("""
            INSERT INTO transactions (transaction_id, account_id, product_id, quantity, total_amount, transacted_at, payment_status) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                (101, 1, 1, 3, 2550.0, "2024-06-01", "SETTLED"),
                (102, 1, 2, 2, 640.0, "2024-06-05", "SETTLED"),
                (103, 2, 4, 1, 1850.0, "2024-06-12", "SETTLED"),
                (104, 2, 5, 1, 600.0, "2024-06-15", "SETTLED"),
                (105, 3, 1, 5, 4250.0, "2024-07-02", "SETTLED"),
                (106, 3, 3, 4, 840.0, "2024-07-08", "SETTLED"),
                (107, 4, 2, 3, 960.0, "2024-07-20", "SETTLED"),
                (108, 5, 1, 2, 1700.0, "2024-08-03", "SETTLED"),
                (109, 5, 3, 6, 1260.0, "2024-08-11", "SETTLED"),
                (110, 1, 4, 2, 3700.0, "2024-08-25", "SETTLED")
            ])
            conn.commit()

    def execute_query(self, sql_query: str) -> ExecutionResult:
        conn = self.get_connection()
        cursor = conn.cursor()

        # Query execution plan
        plan_rows = []
        try:
            cursor.execute(f"EXPLAIN QUERY PLAN {sql_query}")
            plan_rows = [f"Detail: {r[3]}" for r in cursor.fetchall()]
        except Exception:
            pass

        start_t = time.perf_counter()
        cursor.execute(sql_query)
        rows_raw = cursor.fetchall()
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = [dict(r) for r in rows_raw]

        return ExecutionResult(
            sql=sql_query,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            duration_ms=elapsed_ms,
            query_plan=plan_rows
        )
