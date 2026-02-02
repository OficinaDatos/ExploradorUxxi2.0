def q_owners() -> str:
    # En Oracle suele haber ALL_TABLES/ALL_TAB_COLUMNS.
    # Algunos entornos restringen ALL_*. Si esto falla, hay que ajustar a lo permitido.
    return """
    SELECT DISTINCT owner
    FROM all_tables
    ORDER BY owner
    """

def q_tables(owner: str) -> str:
    return f"""
    SELECT table_name
    FROM all_tables
    WHERE owner = '{owner.upper()}'
    ORDER BY table_name
    """

def q_columns(owner: str, table: str) -> str:
    return f"""
    SELECT column_name, data_type, data_length, nullable
    FROM all_tab_columns
    WHERE owner = '{owner.upper()}'
      AND table_name = '{table.upper()}'
    ORDER BY column_id
    """

def q_ddl(owner: str, table: str) -> str:
    # DBMS_METADATA puede estar bloqueado. Si lo está, esto va a fallar y devolvemos error claro.
    return f"""
    SELECT DBMS_METADATA.GET_DDL('TABLE','{table.upper()}','{owner.upper()}') AS ddl
    FROM DUAL
    """

def q_preview(owner: str, table: str, limit: int = 50) -> str:
    limit = max(1, min(int(limit), 200))
    return f"""
    SELECT *
    FROM {owner.upper()}.{table.upper()}
    FETCH FIRST {limit} ROWS ONLY
    """
