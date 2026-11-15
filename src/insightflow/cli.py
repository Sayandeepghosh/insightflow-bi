import argparse
import sys
import json
from .database import DatabaseManager
from .security import SQLSecurityValidator
from .engine import QueryEngine

def main():
    parser = argparse.ArgumentParser(
        prog="insightflow",
        description="InsightFlow BI CLI: Natural language to relational SQL executor."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Query subcommand
    query_p = subparsers.add_parser("query", help="Execute analytical natural language prompt.")
    query_p.add_argument("prompt", help="Natural language question, e.g. 'top revenue products'")
    query_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # Serve subcommand
    serve_p = subparsers.add_parser("serve", help="Start FastAPI REST server.")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    db = DatabaseManager(":memory:")
    db.seed_default_tables()
    engine = QueryEngine(db, SQLSecurityValidator())

    if args.command == "query":
        res = engine.execute_prompt(args.prompt)
        if args.json:
            print(json.dumps(res.__dict__, indent=2))
        else:
            print(f"\nPrompt: {res.prompt}")
            print(f"Status: {'VALID' if res.is_safe else 'REJECTED'} (Latency: {res.duration_ms} ms)")
            print("-" * 65)
            print(f"Generated SQL: {res.generated_sql}")
            print(f"Explanation:   {res.explanation}")
            print("-" * 65)
            if res.rows:
                header = " | ".join(f"{c:<20}" for c in res.columns)
                print(header)
                print("-" * len(header))
                for row in res.rows:
                    line = " | ".join(f"{str(row.get(c, '')):<20}" for c in res.columns)
                    print(line)
            else:
                print("No rows returned.")

    elif args.command == "serve":
        import uvicorn
        from .api import app
        uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
