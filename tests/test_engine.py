from insightflow.database import DatabaseManager
from insightflow.engine import QueryEngine

def test_engine_prompt_execution():
    db = DatabaseManager(":memory:")
    db.seed_default_tables()
    engine = QueryEngine(db)

    res = engine.execute_prompt("Show me our top revenue products")
    assert res.is_safe is True
    assert res.row_count > 0
    assert "total_revenue" in res.columns
    assert res.rows[0]["product_name"] is not None
