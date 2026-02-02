def q_owners() -> str:
    # Incluye owners que tengan TABLAS o VISTAS.
    # En UXXI cloud suele haber owners que solo aparecen en ALL_VIEWS (ej: UXXIAC).
    return """
    SELECT owner FROM (
        SELECT DISTINCT owner FROM all_tables
        UNION
        SELECT DISTINCT owner FROM all_views
    )
    ORDER BY owner
    """


def q_tables(owner: str) -> str:
    # Devuelve una lista simple de nombres (tablas + vistas) para no romper el frontend.
    o = owner.upper()
    return f"""
    SELECT name FROM (
        SELECT table_name AS name
        FROM all_tables
        WHERE owner = '{o}'
        UNION
        SELECT view_name AS name
        FROM all_views
        WHERE owner = '{o}'
    )
    ORDER BY name
    """


def q_columns(owner: str, table: str) -> str:
    # Funciona tanto para tablas como para vistas.
    return f"""
    SELECT column_name, data_type, data_length, nullable
    FROM all_tab_columns
    WHERE owner = '{owner.upper()}'
      AND table_name = '{table.upper()}'
    ORDER BY column_id
    """


def q_ddl(owner: str, table: str) -> str:
    # Intenta devolver DDL de TABLE y, si no existe, de VIEW.
    # Si DBMS_METADATA está bloqueado, fallará y main.py hará fallback a ALL_VIEWS.TEXT.
    o = owner.upper()
    t = table.upper()
    return f"""
    SELECT ddl FROM (
        SELECT DBMS_METADATA.GET_DDL('TABLE','{t}','{o}') AS ddl FROM dual
        UNION ALL
        SELECT DBMS_METADATA.GET_DDL('VIEW','{t}','{o}')  AS ddl FROM dual
    )
    WHERE ddl IS NOT NULL
    FETCH FIRST 1 ROWS ONLY
    """


def q_view_text(owner: str, view: str) -> str:
    # Fallback seguro para vistas: devuelve el texto/definición desde ALL_VIEWS
    return f"""
    SELECT TEXT AS ddl
    FROM ALL_VIEWS
    WHERE OWNER = '{owner.upper()}'
      AND VIEW_NAME = '{view.upper()}'
    """


def q_preview(owner: str, table: str, limit: int = 50) -> str:
    # Más compatible que FETCH FIRST (algunos entornos fallan o no lo permiten).
    limit = max(1, min(int(limit), 200))
    return f"""
    SELECT *
    FROM {owner.upper()}.{table.upper()}
    WHERE ROWNUM <= {limit}
    """



