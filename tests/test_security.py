from insightflow.security import SQLSecurityValidator

def test_security_valid_select_enforces_limit():
    validator = SQLSecurityValidator(max_limit=50)
    res = validator.validate_and_sanitize("SELECT * FROM products")
    assert res.is_safe is True
    assert "LIMIT 50" in res.sanitized_sql

def test_security_blocks_drop_and_delete():
    validator = SQLSecurityValidator()
    # Non-select statement
    res1 = validator.validate_and_sanitize("DROP TABLE accounts")
    assert res1.is_safe is False
    assert "SELECT and WITH" in res1.violation_reason

    # Injection inside select payload
    res2 = validator.validate_and_sanitize("SELECT * FROM accounts WHERE id = (DELETE FROM accounts)")
    assert res2.is_safe is False
    assert "DELETE" in res2.violation_reason

def test_security_blocks_chained_queries():
    validator = SQLSecurityValidator()
    res = validator.validate_and_sanitize("SELECT 1; SELECT 2")
    assert res.is_safe is False
    assert "Multiple SQL statements" in res.violation_reason
