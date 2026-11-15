# insightflow-bi

[![CI Tests](https://github.com/Sayandeepghosh/insightflow-bi/actions/workflows/ci.yml/badge.svg)](https://github.com/Sayandeepghosh/insightflow-bi/actions)
[![Live Demo](https://img.shields.io/badge/Demo-Live%20GitHub%20Pages-blue.svg)](https://sayandeepghosh.github.io/insightflow-bi/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)]()
[![Security](https://img.shields.io/badge/Security-AST%20Validated%20Read--Only-green.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

Production-grade Text-to-SQL business intelligence microservice engineered with strict AST query safety validation, automatic schema introspection, and SQLite analytical execution.

🔗 **Live Interactive SQL Playground:** [https://sayandeepghosh.github.io/insightflow-bi/](https://sayandeepghosh.github.io/insightflow-bi/)

---

## Architectural Pipeline

```text
  [ User Analytical Prompt: "Show our top products by revenue" ]
                              │
                              ▼
                [ Query Translation Engine ]
                              │
                              ▼
          [ SQL Security Validator & AST Sanitizer ]
            - Rejects DDL/DML mutations (DROP, DELETE, UPDATE, ALTER)
            - Prohibits multiple semicolon-chained statements
            - Automatically clamps query LIMIT (default: 100 rows)
                              │
                              ▼
          [ Relational SQLite Engine + Query Plan Analysis ]
                              │
                              ▼
          [ Formatted Response: Columns + Rows + Execution Telemetry ]
```

---

## Key Features

- **Schema Introspection:** Automatically inspects relational tables, primary keys, foreign keys, and row counts via `PRAGMA` introspection.
- **SQL Injection & Mutation Defense:** Rejects any non-SELECT operations and prevents dangerous chained payloads.
- **Query Plan Telemetry:** Captures SQLite `EXPLAIN QUERY PLAN` logs and millisecond-level execution duration for every query.
- **Dual Interfaces:** Fully functional CLI tool (`insightflow`) and asynchronous FastAPI REST endpoints.

---

## Quickstart

```bash
git clone https://github.com/Sayandeepghosh/insightflow-bi.git
cd insightflow-bi

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -e .
```

---

## CLI Usage

### Querying the Database
```bash
python -m insightflow.cli query "Show our top products ranked by gross revenue"
```

Output:
```text
Prompt: Show our top products ranked by gross revenue
Status: VALID (Latency: 0.12 ms)
-----------------------------------------------------------------
Generated SQL: SELECT p.product_name, p.category, SUM(t.quantity) AS total_units_sold, ROUND(SUM(t.total_amount), 2) AS total_revenue FROM transactions t JOIN products p ON t.product_id = p.product_id GROUP BY p.product_id ORDER BY total_revenue DESC LIMIT 5
Explanation:   Aggregated top-performing products ranked by gross transactional revenue.
-----------------------------------------------------------------
product_name         | category             | total_units_sold     | total_revenue       
-----------------------------------------------------------------------------------------
Autonomous Agent ... | Software             | 10                   | 8500.0              
Dedicated GPU Com... | Infrastructure       | 3                    | 5550.0              
Vector Embedding ... | Infrastructure       | 5                    | 1600.0              
```

### Launching the REST Service
```bash
python -m insightflow.cli serve --port 8000
```
Open `http://127.0.0.1:8000/docs` to test endpoints via Swagger UI.

---

## REST Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health and active database location |
| `GET` | `/v1/schema` | Live schema introspection (tables, columns, foreign keys) |
| `GET` | `/v1/samples` | List of tested executive prompt templates |
| `POST` | `/v1/query` | Translates natural language prompt, validates, and returns data |

---

## Running the Test Suite

```bash
pytest tests/ -v
```

---

## License
MIT
