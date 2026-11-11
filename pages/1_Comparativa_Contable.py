import streamlit as st
from ui import inject_css, md, page_header, empty_state

# Los estilos van primero: así la página se ve con el diseño del portal desde el
# primer instante, antes de cargar las librerías pesadas.
st.set_page_config(
    page_title="Comparativa Contable",
    page_icon=":material/search:",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

from sesion import requerir_sesion
requerir_sesion()

import pandas as pd
import io
from datetime import datetime


# ── Funciones ────────────────────────────────────────────────────────────────

def cargar_extracto(archivo) -> tuple:
    """
    Lee el extracto bancario (CSV, TXT o Excel).
    Devuelve:
      - serie_col_i : columna I (índice 8) con los montos
      - desc_col_g  : columna G (índice 6) con descripciones
    Excluye filas de saldo (SALDO INICIAL, SALDO DIA, SALDO FINAL).
    """
    nombre = archivo.name.lower()
    es_excel = nombre.endswith(".xlsx") or nombre.endswith(".xls")

    if es_excel:
        contenido = archivo.read()
        df = pd.read_excel(io.BytesIO(contenido), sheet_name=0, header=None)
    else:
        contenido = archivo.read()
        df = None
        for enc in ["latin1", "utf-8", "cp1252"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(contenido),
                    encoding=enc,
                    sep=None,
                    engine="python",
                    header=None,
                )
                break
            except Exception:
                continue

    if df is None or df.shape[1] < 9:
        st.error(
            f"El archivo no tiene suficientes columnas (se necesitan al menos 9). "
            f"Columnas detectadas: {df.shape[1] if df is not None else 0}"
        )
        return None, None

    # Excluir filas de saldo que no son transacciones reales
    desc_raw = df[6].fillna("").astype(str).str.strip().str.upper()
    mask_saldo = desc_raw.str.startswith("SALDO")
    df = df[~mask_saldo].copy()

    # Valor y descripción se filtran con la MISMA máscara: si solo se descartara
    # el valor (p. ej. la fila de encabezados), las descripciones quedarían corridas.
    col_i    = pd.to_numeric(df[8], errors="coerce")
    desc_col = df[6].fillna("").astype(str).str.strip()
    mask_num = col_i.notna()

    return (col_i[mask_num].reset_index(drop=True),
            desc_col[mask_num].reset_index(drop=True))


def cargar_extracto_formato2(archivo) -> tuple:
    """
    Lee el extracto bancario en el formato "banco" (con bloques de
    metadatos arriba y tabla de movimientos con encabezados reales:
    FECHA | DESCRIPCIÓN | SUCURSAL | DCTO. | VALOR | SALDO).

    Detecta automáticamente la fila de encabezados y limpia los valores
    numéricos (vienen como texto con comas, ej. "12,069,906.60").

    Devuelve la misma estructura que cargar_extracto():
      - col_i    : valores numéricos de la columna VALOR
      - desc_col : descripciones de la columna DESCRIPCIÓN
    """
    contenido = archivo.read()
    df_raw = pd.read_excel(io.BytesIO(contenido), sheet_name=0, header=None)

    header_row = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().lower() for v in row.values]
        tiene_desc = any("descrip" in v for v in vals)
        tiene_valor = any("valor" in v and "saldo" not in v for v in vals)
        if tiene_desc and tiene_valor:
            header_row = i
            break

    if header_row is None:
        st.error(
            "No se encontró la fila de encabezados (FECHA / DESCRIPCIÓN / VALOR) "
            "en el Excel del extracto."
        )
        return None, None

    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = [str(c).strip() for c in df_raw.iloc[header_row].values]

    col_desc = next((c for c in df.columns if "descrip" in c.lower()), None)
    col_valor = next(
        (c for c in df.columns if "valor" in c.lower() and "saldo" not in c.lower()),
        None,
    )

    if not col_desc or not col_valor:
        st.error(
            f"No se encontraron columnas Descripción/Valor. "
            f"Columnas disponibles: {list(df.columns)}"
        )
        return None, None

    desc_col = df[col_desc].fillna("").astype(str).str.strip()

    valor_raw = (
        df[col_valor]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
    )
    col_i = pd.to_numeric(valor_raw, errors="coerce")

    # Excluir filas sin valor numérico (pies de página, separadores, etc.)
    # y filas de saldo que no son transacciones reales
    desc_upper = desc_col.str.upper()
    mask_valido = col_i.notna() & ~desc_upper.str.startswith("SALDO") & (desc_col != "")

    col_i = col_i[mask_valido]
    desc_col = desc_col[mask_valido]

    return col_i.reset_index(drop=True), desc_col.reset_index(drop=True)


def cargar_excel(archivo) -> tuple:
    """
    Lee el libro contable Excel.
    Detecta la fila de encabezados buscando 'Crédito' o 'Credito'.
    Devuelve (df, col_debito, col_credito, col_tercero, col_desc).
    """
    df_raw = pd.read_excel(archivo, sheet_name=0, header=None)

    header_row = None
    for i, row in df_raw.iterrows():
        vals = [str(v).strip().lower() for v in row.values]
        if any("cr" in v and "dito" in v for v in vals):
            header_row = i
            break

    if header_row is None:
        st.error("No se encontró la fila de encabezados en el Excel.")
        return None

    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = [str(c).strip() for c in df_raw.iloc[header_row].values]

    col_debito = next(
        (c for c in df.columns if "d" in c.lower() and "bito" in c.lower()), None
    )
    col_credito = next(
        (c for c in df.columns if "cr" in c.lower() and "dito" in c.lower()), None
    )

    if not col_debito or not col_credito:
        st.error(
            f"No se encontraron columnas Débito/Crédito. "
            f"Columnas disponibles: {list(df.columns)}"
        )
        return None

    col_tercero = next(
        (c for c in df.columns if "tercero" in c.lower()), None
    )

    col_desc = next(
        (c for c in df.columns if "descrip" in c.lower()), None
    )

    cols = [col_debito, col_credito]
    if col_tercero:
        cols.append(col_tercero)
    if col_desc and col_desc not in cols:
        cols.append(col_desc)

    resultado = df[cols].copy()
    resultado[col_debito]  = pd.to_numeric(resultado[col_debito],  errors="coerce")
    resultado[col_credito] = pd.to_numeric(resultado[col_credito], errors="coerce")
    resultado = resultado.dropna(subset=[col_debito, col_credito], how="all")
    resultado.reset_index(drop=True, inplace=True)
    return resultado, col_debito, col_credito, col_tercero, col_desc


ESTADO_BANCARIO = "Gasto bancario"

# Conceptos del extracto que el libro registra acumulados (se buscan por "contiene")
CONCEPTOS_BANCARIOS = [
    "IMPTO GOBIERNO 4X1000",
    "GMF",
    "CUOTA MANEJO",
    "COBRO IVA",
    "SERVICIO PAGO",
    "COMISION",
    "ABONO INTERESES",
    "AJUSTE INTERES",
]


def es_gasto_bancario(descripcion: str, conceptos) -> bool:
    desc = str(descripcion).upper()
    return any(c.upper() in desc for c in conceptos)


def comparar(
    serie_csv: pd.Series,
    desc_csv: pd.Series,
    df_excel: pd.DataFrame,
    col_debito: str,
    col_credito: str,
    col_tercero: str,
    tolerancia: float,
    conceptos_banco=(),
) -> pd.DataFrame:
    """
    Para CADA valor del CSV (en valor absoluto) busca coincidencia
    en la columna Débito Y en la columna Crédito del Excel.

    Casos de estado:
      En Débito        → encontrado solo en Débito
      En Crédito       → encontrado solo en Crédito
      En Débito y Crédito → encontrado en ambas columnas
      Gasto bancario   → no está, pero su descripción es de un concepto de
                            conceptos_banco (el libro lo registra acumulado)
      No encontrado    → no está en ninguna

    También reporta el Nombre del Tercero de cada coincidencia.
    """
    # Construir mapas  valor_redondeado → nombre_tercero   para cada columna
    def build_map(col_name):
        m = {}
        for _, row in df_excel.iterrows():
            v = row[col_name]
            if pd.isna(v) or v == 0:
                continue
            vr = round(float(v), 2)
            if vr not in m:
                nombre = (
                    str(row[col_tercero]).strip()
                    if col_tercero and pd.notna(row[col_tercero])
                    else ""
                )
                m[vr] = nombre
        return m

    map_debito  = build_map(col_debito)
    map_credito = build_map(col_credito)

    set_debito  = set(map_debito.keys())
    set_credito = set(map_credito.keys())

    filas = []
    for idx in range(len(serie_csv)):
        val   = serie_csv.iloc[idx]
        desc  = str(desc_csv.iloc[idx]).strip() if idx < len(desc_csv) else ""

        val_r   = round(float(val), 2)
        val_abs = round(abs(val_r), 2)

        # Buscar en Débito
        match_d = next(
            (v for v in set_debito if abs(val_abs - v) <= tolerancia), None
        )
        # Buscar en Crédito
        match_c = next(
            (v for v in set_credito if abs(val_abs - v) <= tolerancia), None
        )

        en_debito  = match_d is not None
        en_credito = match_c is not None

        nombre_d = map_debito.get(match_d, "")  if en_debito  else ""
        nombre_c = map_credito.get(match_c, "") if en_credito else ""

        # Estado consolidado
        if en_debito and en_credito:
            estado = "En Débito y Crédito"
        elif en_debito:
            estado = "En Débito"
        elif en_credito:
            estado = "En Crédito"
        elif es_gasto_bancario(desc, conceptos_banco):
            estado = ESTADO_BANCARIO
        else:
            estado = "No encontrado"

        # Nombre único (si coincide en ambas, mostrar el más informativo)
        nombre_tercero = nombre_d or nombre_c

        filas.append(
            {
                "Valor CSV (Col I)":   val_r,
                "Descripción CSV":     desc,
                f"En {col_debito}":    "Sí" if en_debito  else "No",
                f"En {col_credito}":   "Sí" if en_credito else "No",
                "Nombre del tercero":  nombre_tercero,
                "Estado":              estado,
            }
        )

    return pd.DataFrame(filas)


def exportar_excel(df_resultado: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Comparativa")
    return buf.getvalue()


# ── UI ───────────────────────────────────────────────────────────────────────

page_header('Comparativa Contable', 'Verifica si los valores del extracto bancario (CSV) están registrados en <strong>Débito</strong> o <strong>Crédito</strong> del libro contable (Excel)', 'search')

# ── Carga de archivos ────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    md('<p class="section-title">[[file-text]] Extracto Bancario (CSV o Excel)</p>', unsafe_allow_html=True)
    st.caption("Columna I · valores del extracto · acepta CSV, TXT o Excel")
    archivo_csv = st.file_uploader(
        "Subir extracto", type=["csv", "txt", "xlsx", "xls"],
        key="csv", label_visibility="collapsed"
    )

    formato_extracto = "clasico"
    if archivo_csv is not None:
        nombre_csv_check = archivo_csv.name.lower()
        es_excel_csv = nombre_csv_check.endswith(".xlsx") or nombre_csv_check.endswith(".xls")
        if es_excel_csv:
            formato_extracto = st.radio(
                "Formato del extracto:",
                ["clasico", "banco"],
                format_func=lambda x: (
                    ":material/description: Formato clásico (columna I)" if x == "clasico"
                    else ":material/account_balance: Formato banco (con encabezados FECHA/DESCRIPCIÓN/VALOR)"
                ),
                horizontal=False,
                key="formato_extracto",
            )

with col2:
    md('<p class="section-title">[[bar-chart]] Libro Contable (Excel)</p>', unsafe_allow_html=True)
    st.caption("Columnas: Débito · Crédito · Nombre del tercero")
    archivo_xlsx = st.file_uploader(
        "Subir Excel", type=["xlsx", "xls"],
        key="xlsx", label_visibility="collapsed"
    )

# ── Opciones avanzadas ───────────────────────────────────────────────────────
with st.expander(":material/tune: Opciones avanzadas"):
    tolerancia = st.number_input(
        "Tolerancia de comparación (diferencia máxima permitida)",
        min_value=0.0,
        max_value=100.0,
        value=0.01,
        step=0.01,
        format="%.2f",
        help="Útil para diferencias por redondeo. Por defecto 0.01",
    )

    md("**:material/account_balance: Gastos bancarios** (el extracto los trae línea a línea y el libro acumulados)")
    conceptos_txt = st.text_area(
        "Conceptos del extracto (uno por línea)",
        value="\n".join(CONCEPTOS_BANCARIOS),
        height=180,
        help="Si la descripción del extracto CONTIENE alguno de estos textos y el "
             "valor no está en el libro, se marca como Gasto bancario y no como faltante.",
    )
    clave_libro = st.text_input(
        "Texto que identifica las filas acumuladas en el libro",
        value="Gastos bancarios",
        help="Se busca en la columna Descripción del libro para cuadrar el total.",
    )
    tol_banco = st.number_input(
        "Tolerancia del cuadre de gastos bancarios",
        min_value=0.0,
        max_value=1000.0,
        value=1.0,
        step=0.5,
        format="%.2f",
        help="Diferencia máxima aceptada entre la suma del extracto y el libro.",
    )
    conceptos_banco = [c.strip() for c in conceptos_txt.splitlines() if c.strip()]

# ── Procesamiento ────────────────────────────────────────────────────────────
if archivo_csv and archivo_xlsx:
    with st.spinner("Procesando archivos..."):
        nombre_csv_actual = archivo_csv.name.lower()
        es_excel_csv_actual = nombre_csv_actual.endswith(".xlsx") or nombre_csv_actual.endswith(".xls")

        if es_excel_csv_actual and formato_extracto == "banco":
            serie_csv, desc_csv = cargar_extracto_formato2(archivo_csv)
        else:
            serie_csv, desc_csv = cargar_extracto(archivo_csv)

        resultado_excel = cargar_excel(archivo_xlsx)

    if serie_csv is None or resultado_excel is None:
        st.stop()

    df_excel, col_debito, col_credito, col_tercero, col_desc = resultado_excel

    df_resultado = comparar(
        serie_csv, desc_csv,
        df_excel, col_debito, col_credito, col_tercero,
        tolerancia, conceptos_banco,
    )

    # ── Métricas ─────────────────────────────────────────────────────────────
    total            = len(df_resultado)
    en_debito        = df_resultado["Estado"].str.contains("Débito").sum()
    en_credito       = df_resultado["Estado"].str.contains("Crédito").sum()
    en_ambos         = df_resultado["Estado"].str.contains("Débito y Crédito").sum()
    no_encontrados   = (df_resultado["Estado"] == "No encontrado").sum()
    bancarios        = (df_resultado["Estado"] == ESTADO_BANCARIO).sum()
    encontrados_tot  = total - no_encontrados
    pct              = round(encontrados_tot / total * 100, 1) if total > 0 else 0

    md("---")
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    with m1:
        md(f"""
        <div class="metric-card">
            <div class="number blue">{total}</div>
            <div class="label">Valores analizados</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        md(f"""
        <div class="metric-card">
            <div class="number green">{en_debito}</div>
            <div class="label">Encontrados en Débito</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        md(f"""
        <div class="metric-card">
            <div class="number orange">{en_credito}</div>
            <div class="label">Encontrados en Crédito</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        md(f"""
        <div class="metric-card">
            <div class="number red">{no_encontrados}</div>
            <div class="label">No encontrados</div>
        </div>""", unsafe_allow_html=True)
    with m5:
        md(f"""
        <div class="metric-card">
            <div class="number purple">{bancarios}</div>
            <div class="label">Gastos bancarios</div>
        </div>""", unsafe_allow_html=True)
    with m6:
        color = "green" if pct == 100 else ("orange" if pct >= 80 else "red")
        md(f"""
        <div class="metric-card">
            <div class="number {color}">{pct}%</div>
            <div class="label">Coincidencia total</div>
        </div>""", unsafe_allow_html=True)

    # ── Tabla resultado ───────────────────────────────────────────────────────
    md('<p class="section-title">[[clipboard-list]] Resultado detallado</p>', unsafe_allow_html=True)

    filtro = st.radio(
        "Mostrar:",
        [
            "Todos",
            "No encontrados",
            ESTADO_BANCARIO,
            "En Débito",
            "En Crédito",
            "En Débito y Crédito",
        ],
        horizontal=True,
    )

    df_mostrar = df_resultado.copy()
    if filtro == "No encontrados":
        df_mostrar = df_mostrar[df_mostrar["Estado"] == "No encontrado"]
    elif filtro == ESTADO_BANCARIO:
        df_mostrar = df_mostrar[df_mostrar["Estado"] == ESTADO_BANCARIO]
    elif filtro == "En Débito":
        df_mostrar = df_mostrar[df_mostrar["Estado"] == "En Débito"]
    elif filtro == "En Crédito":
        df_mostrar = df_mostrar[df_mostrar["Estado"] == "En Crédito"]
    elif filtro == "En Débito y Crédito":
        df_mostrar = df_mostrar[df_mostrar["Estado"] == "En Débito y Crédito"]

    def colorear_fila(row):
        estado = str(row["Estado"])
        if "No encontrado" in estado:
            return ["background-color: rgba(220, 38, 38, .12)"] * len(row)
        elif ESTADO_BANCARIO in estado:
            return ["background-color: rgba(124, 58, 237, .13)"] * len(row)
        elif "Débito y Crédito" in estado:
            return ["background-color: rgba(37, 99, 235, .13)"] * len(row)
        elif "Débito" in estado:
            return ["background-color: rgba(22, 163, 74, .12)"] * len(row)
        elif "Crédito" in estado:
            return ["background-color: rgba(234, 179, 8, .15)"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_mostrar.style.apply(colorear_fila, axis=1),
        use_container_width=True,
        height=440,
    )

    # ── Leyenda de colores ────────────────────────────────────────────────────
    st.caption(
        "Verde = encontrado en Débito · Amarillo = encontrado en Crédito · "
        "Azul = encontrado en ambas · Morado = gasto bancario (acumulado en el libro) · "
        "Rojo = no encontrado"
    )

    # ── Cuadre de gastos bancarios contra las filas acumuladas del libro ─────
    if bancarios > 0:
        md('<p class="section-title">[[landmark]] Cuadre de gastos bancarios</p>',
                    unsafe_allow_html=True)

        df_banco = df_resultado[df_resultado["Estado"] == ESTADO_BANCARIO]
        vals_banco = df_banco["Valor CSV (Col I)"]
        ext_abonos = round(float(vals_banco[vals_banco > 0].sum()), 2)
        ext_cargos = round(float(-vals_banco[vals_banco < 0].sum()), 2)

        if col_desc:
            mask_lib = (
                df_excel[col_desc].astype(str).str.upper()
                .str.contains(clave_libro.strip().upper(), regex=False, na=False)
            )
        else:
            mask_lib = pd.Series(False, index=df_excel.index)

        if not clave_libro.strip() or not mask_lib.any():
            st.info(
                f"No se encontraron filas con «{clave_libro}» en el libro, así que no "
                "se puede cuadrar el total. Los gastos bancarios del extracto suman: "
                f"abonos {ext_abonos:,.2f} · cargos {ext_cargos:,.2f}."
            )
        else:
            lib_deb = round(float(df_excel.loc[mask_lib, col_debito].fillna(0).sum()), 2)
            lib_cre = round(float(df_excel.loc[mask_lib, col_credito].fillna(0).sum()), 2)
            filas = []
            for nombre, ext, lib in [
                ("Abonos del extracto vs Débito del libro", ext_abonos, lib_deb),
                ("Cargos del extracto vs Crédito del libro", ext_cargos, lib_cre),
            ]:
                dif = round(ext - lib, 2)
                filas.append({
                    "Concepto": nombre,
                    "Extracto": ext,
                    "Libro (acumulado)": lib,
                    "Diferencia": dif,
                    "Estado": "Cuadra" if abs(dif) <= tol_banco else "No cuadra",
                })
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
            st.caption(
                f"{len(df_banco)} movimientos del extracto · {int(mask_lib.sum())} filas "
                f"«{clave_libro}» en el libro · tolerancia {tol_banco:,.2f}"
            )

    # ── Exportar ──────────────────────────────────────────────────────────────
    md("---")
    col_exp1, col_exp2, _ = st.columns([1, 1, 3])

    with col_exp1:
        xlsx_bytes = exportar_excel(df_resultado)
        st.download_button(
            label=":material/download: Descargar Excel",
            data=xlsx_bytes,
            file_name=f"comparativa_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_exp2:
        csv_bytes = df_resultado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=":material/download: Descargar CSV",
            data=csv_bytes,
            file_name=f"comparativa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Vista previa de archivos fuente ──────────────────────────────────────
    with st.expander(":material/visibility: Vista previa de archivos cargados"):
        t1, t2 = st.tabs(["CSV — Valores analizados", "Excel — Débito & Crédito"])
        with t1:
            prev_csv = pd.DataFrame(
                {"Descripción (Col G)": desc_csv, "Valor (Col I)": serie_csv}
            )
            st.dataframe(prev_csv, use_container_width=True, height=300)
        with t2:
            cols_preview = [c for c in [col_tercero, col_debito, col_credito] if c]
            st.dataframe(df_excel[cols_preview], use_container_width=True, height=300)

else:
    empty_state('Carga los dos archivos para iniciar la comparativa', 'CSV con la columna I · Excel con Débito, Crédito y Nombre del tercero')
