from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from .uxxi_client import UXXIClient
from . import sql_queries as Q

load_dotenv()

app = FastAPI(title="UXXI Explorer API", version="1.0.0")

allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins] if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

def run_rows(sql: str):
    c = UXXIClient()
    try:
        payload = c.sql(sql)
        return UXXIClient.to_rows(payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        c.close()

@app.get("/meta/owners")
def owners():
    return {"owners": [r["owner"] for r in run_rows(Q.q_owners())]}

@app.get("/meta/tables")
def tables(owner: str = Query(..., min_length=1)):
    rows = run_rows(Q.q_tables(owner))
    return {"owner": owner, "tables": [r["table_name"] for r in rows]}

@app.get("/meta/columns")
def columns(owner: str, table: str):
    return {"owner": owner, "table": table, "columns": run_rows(Q.q_columns(owner, table))}

@app.get("/meta/ddl")
def ddl(owner: str, table: str):
    rows = run_rows(Q.q_ddl(owner, table))
    ddl_value = rows[0].get("ddl") if rows else None
    return {"owner": owner, "table": table, "ddl": ddl_value}

@app.get("/data/preview")
def preview(owner: str, table: str, limit: int = 50):
    return {"owner": owner, "table": table, "rows": run_rows(Q.q_preview(owner, table, limit))}
