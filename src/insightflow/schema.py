import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ColumnMetadata:
    cid: int
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool

@dataclass
class TableMetadata:
    table_name: str
    columns: List[ColumnMetadata]
    foreign_keys: List[Dict[str, str]]
    row_count: int

class SchemaInspector:
    """Introspects SQLite relational schema, primary keys, and foreign key relationships."""

    @staticmethod
    def inspect(connection: sqlite3.Connection) -> Dict[str, TableMetadata]:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        schema: Dict[str, TableMetadata] = {}

        for table in tables:
            # Columns
            cursor.execute(f"PRAGMA table_info({table});")
            cols = [
                ColumnMetadata(
                    cid=r[0],
                    name=r[1],
                    data_type=r[2],
                    is_nullable=(r[3] == 0),
                    is_primary_key=(r[5] == 1)
                )
                for r in cursor.fetchall()
            ]

            # Foreign Keys
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = [
                {"column": r[3], "referenced_table": r[2], "referenced_column": r[4]}
                for r in cursor.fetchall()
            ]

            # Row Count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]

            schema[table] = TableMetadata(
                table_name=table,
                columns=cols,
                foreign_keys=fks,
                row_count=row_count
            )

        return schema
