from insightflow.database import DatabaseManager
from insightflow.schema import SchemaInspector

def test_database_seeding_and_schema():
    db = DatabaseManager(":memory:")
    db.seed_default_tables()
    conn = db.get_connection()

    schema = SchemaInspector.inspect(conn)
    assert "accounts" in schema
    assert "products" in schema
    assert "transactions" in schema
    assert schema["products"].row_count == 5
    assert schema["transactions"].row_count == 10
