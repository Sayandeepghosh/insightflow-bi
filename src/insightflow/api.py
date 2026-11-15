import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from .database import DatabaseManager
from .security import SQLSecurityValidator
from .schema import SchemaInspector
from .engine import QueryEngine
from .config import Settings

app = FastAPI(
    title="InsightFlow BI API",
    description="Text-to-SQL business intelligence microservice with AST query safety validation",
    version="0.1.0"
)

# Initialize persistence
settings = Settings()
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)
db_file = os.path.join(data_dir, "insightflow.db")

db_manager = DatabaseManager(db_file)
db_manager.seed_default_tables()

security_validator = SQLSecurityValidator(max_limit=settings.max_query_limit)
query_engine = QueryEngine(db_manager, security_validator)

class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=2, description="Natural language analytical question")
    raw_sql: Optional[str] = Field(default=None, description="Optional raw SQL string to execute directly")

class QueryResponse(BaseModel):
    prompt: str
    generated_sql: str
    is_safe: bool
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    duration_ms: float
    query_plan: List[str]
    explanation: str

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "InsightFlow BI API",
        "database": db_file,
        "enforced_max_limit": settings.max_query_limit
    }

@app.get("/v1/schema")
def inspect_schema():
    conn = db_manager.get_connection()
    schema = SchemaInspector.inspect(conn)
    return {
        "tables": {
            tbl_name: {
                "columns": [c.__dict__ for c in tbl_meta.columns],
                "foreign_keys": tbl_meta.foreign_keys,
                "row_count": tbl_meta.row_count
            }
            for tbl_name, tbl_meta in schema.items()
        }
    }

@app.get("/v1/samples")
def sample_prompts():
    return {
        "suggested_prompts": [
            "Show our top products ranked by gross revenue",
            "Calculate regional transaction revenue and account volume",
            "Who are our top 5 corporate accounts by lifetime spend?",
            "What is our monthly transaction volume and revenue trend?",
            "Display revenue breakdown across product categories"
        ]
    }

@app.post("/v1/query", response_model=QueryResponse)
def execute_query(req: QueryRequest):
    result = query_engine.execute_prompt(req.prompt, raw_sql=req.raw_sql)
    if not result.is_safe:
        raise HTTPException(status_code=400, detail=result.explanation)

    return QueryResponse(
        prompt=result.prompt,
        generated_sql=result.generated_sql,
        is_safe=result.is_safe,
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        duration_ms=result.duration_ms,
        query_plan=result.query_plan,
        explanation=result.explanation
    )
