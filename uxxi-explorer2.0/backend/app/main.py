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

def pick(row: dict, *keys: str):
    """
    Obtiene un valor de un dict sin importar mayúsculas/minúsculas.
    Ej: pick(r, "owner") funciona con owner / OWNER.
    """
    for k in keys:
        if k in row:
            return row[k]
        lk = k.lower()
        if lk in row:
            return row[lk]
        uk = k.upper()
        if uk in row:
            return row[uk]
    return None

@app.get("/meta/owners")
def owners():
    rows = run_rows(Q.q_owners())
    owners_list = []
    for r in rows:
        v = pick(r, "owner")
        if v:
            owners_list.append(v)
    return {"owners": owners_list}

@app.get("/meta/tables")
def tables(owner: str = Query(..., min_length=1)):
    rows = run_rows(Q.q_tables(owner))
    # soporta q_tables antiguo (table_name) o nuevo (name)
    tables_list = []
    for r in rows:
        v = pick(r, "table_name", "name")
        if v:
            tables_list.append(v)
    return {"owner": owner, "tables": tables_list}

@app.get("/meta/columns")
def columns(owner: str, table: str):
    return {"owner": owner, "table": table, "columns": run_rows(Q.q_columns(owner, table))}

@app.get("/meta/ddl")
def ddl(owner: str, table: str):
    # 1) Intento principal: DBMS_METADATA (TABLE/VIEW según tu q_ddl)
    try:
        rows = run_rows(Q.q_ddl(owner, table))
        ddl_value = pick(rows[0], "ddl") if rows else None
        if ddl_value:
            return {"owner": owner, "table": table, "ddl": ddl_value}
    except HTTPException:
        # Si DBMS_METADATA falla por permisos u otro problema, vamos a fallback
        pass

    # 2) Fallback: si es vista, devolver definición desde ALL_VIEWS.TEXT
    try:
        rows2 = run_rows(Q.q_view_text(owner, table))
        ddl_value2 = pick(rows2[0], "ddl") if rows2 else None
        return {"owner": owner, "table": table, "ddl": ddl_value2}
    except Exception as e:
        return {"owner": owner, "table": table, "ddl": None, "note": f"No se pudo obtener DDL: {e}"}

@app.get("/data/preview")
def preview(owner: str, table: str, limit: int = 50):
    return {"owner": owner, "table": table, "rows": run_rows(Q.q_preview(owner, table, limit))}

