import streamlit as st
from ui import inject_css, md, page_header, empty_state

# Los estilos van primero: así la página se ve con el diseño del portal desde el
# primer instante, antes de cargar las librerías pesadas.
st.set_page_config(
    page_title="Anexos EEFF – ERI y ESF",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
import datetime
import estados as E


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
MESES_ORDEN = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
               "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
MESES_ABREV = {"ENERO":"Ene","FEBRERO":"Feb","MARZO":"Mar","ABRIL":"Abr",
               "MAYO":"May","JUNIO":"Jun","JULIO":"Jul","AGOSTO":"Ago",
               "SEPTIEMBRE":"Sep","OCTUBRE":"Oct","NOVIEMBRE":"Nov","DICIEMBRE":"Dic"}

GRUPOS_ERI = ["INGRESOS DE ACTIVIDADES ORDINARIAS","OTROS INGRESOS",
              "GASTOS DE ADMINISTRACION","OTROS GASTOS",
              "INGRESOS FINANCIEROS","GASTOS FINANCIEROS","PROVISION DE IMPUESTOS"]

GRUPOS_LABEL_ERI = {
    "INGRESOS DE ACTIVIDADES ORDINARIAS":"Ing. Ordinarios",
    "OTROS INGRESOS":"Otros Ingresos","GASTOS DE ADMINISTRACION":"Gtos. Admón.",
    "OTROS GASTOS":"Otros Gastos","INGRESOS FINANCIEROS":"Ing. Financieros",
    "GASTOS FINANCIEROS":"Gtos. Financieros","PROVISION DE IMPUESTOS":"Prov. Impuestos",
}
COLORES_ERI = {
    "INGRESOS DE ACTIVIDADES ORDINARIAS":"#2ecc71","OTROS INGRESOS":"#27ae60",
    "GASTOS DE ADMINISTRACION":"#e74c3c","OTROS GASTOS":"#c0392b",
    "INGRESOS FINANCIEROS":"#3498db","GASTOS FINANCIEROS":"#e67e22",
    "PROVISION DE IMPUESTOS":"#9b59b6","Total general":"#2c3e50",
}

GRUPOS_ESF_ACTIVO = [
    "EFECTIVO Y EQUIVALENTE AL EFECTIVO",
    "CUENTAS COMERCIALES POR COBRAR Y OTRAS CUENTAS POR COBRAR CORRIENTES",
    "CUENTAS POR COBRAR A PARTES RELACIONADAS",
    "ACTIVOS POR IMPUESTOS",
    "ACTIVOS POR IMPUESTOS DIFERIDOS",
    "OTROS ACTIVOS FINANCIEROS NO CTE",
]
GRUPOS_ESF_PASIVO = [
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR NO CORRIENTES",
    "CUENTAS POR PAGAR A PARTES RELACIONADAS",
    "PASIVOS POR IMPUESTOS",
    "PASIVOS POR IMPUESTOS DIFERIDOS",
    "OTROS PASIVOS NO FINANCIEROS ",
    "BENEFICIOS A LOS EMPLEADOS",
]
GRUPOS_ESF_ORDEN = GRUPOS_ESF_ACTIVO + GRUPOS_ESF_PASIVO

GRUPOS_LABEL_ESF = {
    "EFECTIVO Y EQUIVALENTE AL EFECTIVO":"Efectivo y Equiv.",
    "CUENTAS COMERCIALES POR COBRAR Y OTRAS CUENTAS POR COBRAR CORRIENTES":"CxC Corrientes",
    "CUENTAS POR COBRAR A PARTES RELACIONADAS":"CxC Partes Rel.",
    "ACTIVOS POR IMPUESTOS":"Activos x Impuestos",
    "ACTIVOS POR IMPUESTOS DIFERIDOS":"Impuestos Diferidos A.",
    "OTROS ACTIVOS FINANCIEROS NO CTE":"Otros Activos Fin.",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR":"CxP Corrientes",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR NO CORRIENTES":"CxP No Corrientes",
    "CUENTAS POR PAGAR A PARTES RELACIONADAS":"CxP Partes Rel.",
    "PASIVOS POR IMPUESTOS":"Pasivos x Impuestos",
    "PASIVOS POR IMPUESTOS DIFERIDOS":"Impuestos Diferidos P.",
    "OTROS PASIVOS NO FINANCIEROS ":"Otros Pasivos",
    "BENEFICIOS A LOS EMPLEADOS":"Beneficios Empleados",
}
COLORES_ESF = {
    "EFECTIVO Y EQUIVALENTE AL EFECTIVO":"#2ecc71",
    "CUENTAS COMERCIALES POR COBRAR Y OTRAS CUENTAS POR COBRAR CORRIENTES":"#27ae60",
    "CUENTAS POR COBRAR A PARTES RELACIONADAS":"#1a9850",
    "ACTIVOS POR IMPUESTOS":"#52b788","ACTIVOS POR IMPUESTOS DIFERIDOS":"#74c69d",
    "OTROS ACTIVOS FINANCIEROS NO CTE":"#95d5b2",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR":"#e74c3c",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR NO CORRIENTES":"#c0392b",
    "CUENTAS POR PAGAR A PARTES RELACIONADAS":"#e57373",
    "PASIVOS POR IMPUESTOS":"#ef9a9a","PASIVOS POR IMPUESTOS DIFERIDOS":"#e67e22",
    "OTROS PASIVOS NO FINANCIEROS ":"#d35400","BENEFICIOS A LOS EMPLEADOS":"#9b59b6",
}

# Nombres para hojas formateadas (alineados con el archivo de referencia)
NOMBRE_ESF = {
    "EFECTIVO Y EQUIVALENTE AL EFECTIVO":                                   "  Efectivo y equivalentes al efectivo",
    "CUENTAS COMERCIALES POR COBRAR Y OTRAS CUENTAS POR COBRAR CORRIENTES": "  Cuentas comerciales por cobrar y otras cuentas por cobrar",
    "CUENTAS POR COBRAR A PARTES RELACIONADAS":                             "  Cuentas por cobrar a partes relacionadas",
    "ACTIVOS POR IMPUESTOS":                                                "  Activos por impuestos",
    "ACTIVOS POR IMPUESTOS DIFERIDOS":                                      "  Activos por impuestos diferidos",
    "OTROS ACTIVOS FINANCIEROS NO CTE":                                     "  Otros activos financieros",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR":              "  Cuentas comerciales por pagar y otras cuentas por pagar",
    "CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR NO CORRIENTES":"  Cuentas comerciales por pagar y otras cuentas por pagar (NC)",
    "CUENTAS POR PAGAR A PARTES RELACIONADAS":                              "  Cuentas por pagar a partes relacionadas",
    "PASIVOS POR IMPUESTOS":                                                "  Pasivos por impuestos",
    "PASIVOS POR IMPUESTOS DIFERIDOS":                                      "  Pasivos por impuestos diferidos",
    "OTROS PASIVOS NO FINANCIEROS ":                                        "  Otros pasivos no financieros",
    "BENEFICIOS A LOS EMPLEADOS":                                           "  Beneficios a los empleados",
}
NOMBRE_ERI = {
    "INGRESOS DE ACTIVIDADES ORDINARIAS": "Ingresos de actividades ordinarias",
    "OTROS INGRESOS":                     "Otros ingresos",
    "GASTOS DE ADMINISTRACION":           "Gastos de administración",
    "OTROS GASTOS":                       "Otros gastos",
    "INGRESOS FINANCIEROS":               "Ingresos financieros",
    "GASTOS FINANCIEROS":                 "Gastos financieros",
    "PROVISION DE IMPUESTOS":             "Ingreso (gasto) por impuesto",
}

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
def fmt_cop(val):
    if pd.isna(val): return "-"
    if val < 0: return f"($ {abs(val):,.0f})"
    return f"$ {val:,.0f}"


_es_mes_anterior = E.es_mes_anterior


@st.cache_data(show_spinner="Procesando archivo…")
def procesar_archivo(file_bytes: bytes):
    """Lee la hoja terceros_ y devuelve un diccionario con todo lo necesario.

    Si el archivo no se puede usar, devuelve {"errores": [...]} con fila, columna y motivo.
    """
    xls = pd.ExcelFile(BytesIO(file_bytes))
    if "terceros_" not in xls.sheet_names:
        return {"errores": [{"fila": None, "columna": "(hoja)",
                             "motivo": "El archivo no contiene la hoja «terceros_»"}], "avisos": []}

    df = pd.read_excel(BytesIO(file_bytes), sheet_name="terceros_", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    errores, avisos = E.validar_entrada(df)
    if errores:
        return {"errores": errores, "avisos": avisos}

    df["Saldo Mes"] = pd.to_numeric(df["Saldo Mes"], errors="coerce").fillna(0)
    df["Grupo"] = E.normalizar_grupos(df["Grupo"])
    df["cod"] = E.codigo_texto(df["Codigo"])

    # ── Separar filas de "período anterior" si existen en la misma hoja ─────
    mask_ant = df["Mes"].apply(lambda m: pd.notna(m) and E.es_mes_anterior(m))
    df_ant = df[mask_ant].copy()
    df = df[~mask_ant & df["Mes"].notna()].copy()

    ant_auto = None
    if not df_ant.empty:
        saldos_ant = {g: df_ant.loc[df_ant["Grupo"] == g, "Saldo Mes"].sum()
                      for g in GRUPOS_ESF_ORDEN}
        totales_ant = {g: df_ant.loc[df_ant["Grupo"] == g, "Saldo Mes"].sum() for g in GRUPOS_ERI}
        ant_auto = {"saldos": saldos_ant, "totales": totales_ant,
                    "patrimonio": E.saldos_patrimonio(df_ant)}

    def build_pivot(df_src, grupos):
        df_f = df_src[df_src["Grupo"].isin(grupos)].drop(columns=["cod"]).copy()
        pivot = df_f.groupby(["Grupo", "Mes"])["Saldo Mes"].sum().unstack(fill_value=0)
        meses_d = [m for m in MESES_ORDEN if m in pivot.columns]
        pivot = pivot.reindex(columns=meses_d, fill_value=0)
        pivot = pivot.reindex([g for g in grupos if g in pivot.index], fill_value=0)
        return pivot, df_f

    # ERI: movimiento mensual; el acumulado es la suma de los meses
    pivot_eri_m, df_eri_raw = build_pivot(df, GRUPOS_ERI)
    pivot_eri = pivot_eri_m.copy()
    pivot_eri["Total general"] = pivot_eri.sum(axis=1)
    total_row = pivot_eri.sum().to_frame().T
    total_row.index = ["Total general"]
    pivot_eri = pd.concat([pivot_eri, total_row])

    # ESF: saldo de cierre de cada mes. Sumar los meses no tiene sentido, por eso no hay "Total general".
    pivot_esf_crudo, df_esf_raw = build_pivot(df, GRUPOS_ESF_ORDEN)
    pres = pivot_esf_crudo.copy()          # presentación: pasivos con signo positivo
    for g in pres.index:
        if g in GRUPOS_ESF_PASIVO:
            pres.loc[g] = -pres.loc[g]
    act_r = [g for g in GRUPOS_ESF_ACTIVO if g in pres.index]
    pas_r = [g for g in GRUPOS_ESF_PASIVO if g in pres.index]
    ta = pres.loc[act_r].sum().to_frame().T; ta.index = ["Total Activo"]
    tp = pres.loc[pas_r].sum().to_frame().T; tp.index = ["Total Pasivo"]
    pivot_esf = pd.concat([pres.loc[act_r], ta, pres.loc[pas_r], tp])

    meses_con_datos = [m for m in MESES_ORDEN if m in pivot_esf_crudo.columns]
    base = df[["Codigo", "cod", "Nombre cuenta", "Nit", "Nombre tercero", "Mes", "Saldo Mes", "Grupo"]].copy()
    return {
        "errores": [], "avisos": avisos, "df_eri_raw": df_eri_raw, "pivot_eri": pivot_eri,
        "df_esf_raw": df_esf_raw, "pivot_esf": pivot_esf, "pivot_esf_crudo": pivot_esf_crudo,
        "ultimo_mes": meses_con_datos[-1] if meses_con_datos else None,
        "ant_auto": ant_auto, "base": base,
    }


def calcular_estados(res, mes):
    """ESF y ERI (con signo de presentación) de un archivo procesado, al mes de corte."""
    eri = E.lineas_eri(E.totales_hasta(res["pivot_eri"], mes))
    esf = E.lineas_esf(E.saldos_en_mes(res["pivot_esf_crudo"], mes),
                       E.saldos_patrimonio(res["base"], mes), eri["util_per"])
    return eri, esf


def calcular_anterior_auto(ant):
    """Lo mismo, a partir de las filas marcadas como período anterior en el mismo archivo."""
    eri = E.lineas_eri(ant["totales"])
    esf = E.lineas_esf(ant["saldos"], ant["patrimonio"], eri["util_per"])
    return eri, esf


@st.cache_data(show_spinner=False)
def calcular_descuadres(base, tolerancia, mes):
    return E.descuadres_jerarquia(base, tolerancia, mes)


# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN EXCEL FORMATEADO
# ══════════════════════════════════════════════════════════════════════════════
FMT_COP_XL  = '_-"$" * #,##0_-;\\-"$" * #,##0_-;_-"$" * "-"_-;_-@_-'
FMT_SUB_XL  = '#,##0_);\\(#,##0\\);"-       "'

def F(bold=False, size=13, name="Calibri"):
    return Font(bold=bold, size=size, name=name)

def A(h="general", v="center"):
    return Alignment(horizontal=h, vertical=v)

def thin():   return Side(border_style="thin")
def double(): return Side(border_style="double")

def set_val(ws, cell_ref, value, bold=False, size=13, fmt=None,
            halign="general", border_bottom=None):
    c = ws[cell_ref]
    c.value = value if value != 0 else (value if value is not None else None)
    c.font  = F(bold=bold, size=size)
    if halign != "general": c.alignment = A(halign)
    if fmt: c.number_format = fmt
    if border_bottom == "thin":   c.border = Border(bottom=thin())
    if border_bottom == "double": c.border = Border(bottom=double())


FMT_FECHA_XL = 'dd/mm/yyyy'


def generar_hoja_esf(ws, empresa, nit, periodo, esf, esf_ant=None, fechas=None):
    """esf / esf_ant: resultado de estados.lineas_esf (valores con signo de presentación).
       esf_ant None → las columnas del período anterior (F/M) quedan en blanco.
       fechas: (fecha del corte actual, fecha del corte anterior) para los encabezados D7/K7 y F7/M7."""
    from openpyxl.styles import PatternFill as _PF
    hay_ant = esf_ant is not None
    esf_azul_osc = _PF("solid", fgColor="1E3A5F")
    esf_azul_med = _PF("solid", fgColor="2E6DA4")
    esf_azul_cla = _PF("solid", fgColor="D6E4F0")

    anchos = {"A":4,"B":49.6,"C":6.1,"D":17.7,"E":2.6,"F":17.7,
              "G":2.6,"H":12.1,"I":49.6,"J":6.1,"K":17.7,"L":2.6,"M":17.7,"N":12}
    for col, w in anchos.items():
        ws.column_dimensions[col].width = w
    for r in range(1, 42):
        ws.row_dimensions[r].height = 15.0
    ws.row_dimensions[1].height = 30
    for r in [2,3,4,5]: ws.row_dimensions[r].height = 22
    for r in [7,8]: ws.row_dimensions[r].height = 18

    _all_cols = list("BCDEFGHIJKLMN")
    for r, txt, bold, sz in [(1,empresa,True,16),(2,nit,False,13),
                              (3,"ESTADO DE SITUACIÓN FINANCIERA",True,15),
                              (4,periodo,False,12),(5,"(En pesos colombianos - $)",False,11)]:
        for col in _all_cols:
            ws[f"{col}{r}"].fill = esf_azul_osc
        c = ws[f"B{r}"]; c.value = txt
        c.font = Font(bold=bold, size=sz, name="Calibri", color="FFFFFF")

    ws.row_dimensions[6].height = 6
    for col in _all_cols:
        ws[f"{col}6"].fill = esf_azul_med
        ws[f"{col}7"].fill = esf_azul_med
        ws[f"{col}8"].fill = esf_azul_med

    f_act, f_ant = fechas if fechas else (periodo, "Período anterior")
    for col, val in [("C","NOTA"),("D",f_act),("F",f_ant),("J","NOTA"),("K",f_act),("M",f_ant)]:
        c = ws[f"{col}7"]; c.value = val
        c.font = Font(bold=True, size=11, name="Calibri", color="FFFFFF")
        c.alignment = A("center")
        if isinstance(val, datetime.date):
            c.number_format = FMT_FECHA_XL
    for col in ["D","F","K","M"]:
        c = ws[f"{col}8"]; c.value = "$"
        c.font = Font(bold=True, size=11, name="Calibri", color="FFFFFF")
        c.alignment = A("center")

    ws.row_dimensions[9].height = 18
    for col in _all_cols:
        ws[f"{col}9"].fill = esf_azul_cla
    ws["B9"].value = "ACTIVOS"
    ws["B9"].font = Font(bold=True, size=13, name="Calibri", color="1E3A5F")
    ws["I9"].value = "PASIVOS Y PATRIMONIO"
    ws["I9"].font = Font(bold=True, size=13, name="Calibri", color="1E3A5F")
    ws["B11"].value = "Activos corrientes:"; ws["B11"].font = F(size=13)
    ws["I11"].value = "Pasivos corrientes:"; ws["I11"].font = F(size=13)

    def lineas(col_et, col_a, col_b, mapa):
        for row_n, g in mapa:
            ws[f"{col_et}{row_n}"].value = NOMBRE_ESF[g]
            ws[f"{col_et}{row_n}"].font = F(size=13)
            ws[f"{col_et}{row_n}"].alignment = A("left")
            for col, src in ((col_a, esf), (col_b, esf_ant)):
                if src is None:
                    continue
                c = ws[f"{col}{row_n}"]
                c.value = src["grupos"].get(g, 0) or None
                c.number_format = FMT_COP_XL
                c.font = F(size=13)

    def subtotal(col_et, col_a, col_b, fila, texto, mapa):
        ws[f"{col_et}{fila}"].value = texto; ws[f"{col_et}{fila}"].font = F(size=13)
        for col, src in ((col_a, esf), (col_b, esf_ant)):
            if src is None:
                continue
            c = ws[f"{col}{fila}"]
            c.value = sum(src["grupos"].get(g, 0) for _, g in mapa)
            c.number_format = FMT_SUB_XL
            c.font = F(size=13); c.border = Border(bottom=thin())

    def total(col_et, col_a, col_b, fila, texto, cols_fill, fn):
        for col in cols_fill:
            ws[f"{col}{fila}"].fill = esf_azul_cla
        ws[f"{col_et}{fila}"].value = texto
        ws[f"{col_et}{fila}"].font = Font(bold=True, size=14, name="Calibri", color="1E3A5F")
        for col, src in ((col_a, esf), (col_b, esf_ant)):
            if src is None:
                continue
            c = ws[f"{col}{fila}"]
            c.value = fn(src); c.number_format = FMT_COP_XL
            c.font = Font(bold=True, size=14, name="Calibri", color="1E3A5F")
            c.border = Border(bottom=double())

    act_cte = [(12,"EFECTIVO Y EQUIVALENTE AL EFECTIVO"), (14,"ACTIVOS POR IMPUESTOS"),
               (15,"CUENTAS COMERCIALES POR COBRAR Y OTRAS CUENTAS POR COBRAR CORRIENTES"),
               (16,"CUENTAS POR COBRAR A PARTES RELACIONADAS")]
    act_nct = [(25,"OTROS ACTIVOS FINANCIEROS NO CTE"), (26,"ACTIVOS POR IMPUESTOS DIFERIDOS")]
    pas_cte = [(12,"OTROS PASIVOS NO FINANCIEROS "), (14,"PASIVOS POR IMPUESTOS"),
               (15,"CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR"),
               (16,"CUENTAS POR PAGAR A PARTES RELACIONADAS"), (18,"BENEFICIOS A LOS EMPLEADOS")]
    pas_nct = [(23,"CUENTAS COMERCIALES POR PAGAR Y OTRAS CUENTAS POR PAGAR NO CORRIENTES"),
               (24,"PASIVOS POR IMPUESTOS DIFERIDOS")]

    lineas("B","D","F",act_cte); subtotal("B","D","F",19,"Total activos corrientes",act_cte)
    ws["B24"].value = "Activos no corrientes:"; ws["B24"].font = F(size=13)
    lineas("B","D","F",act_nct); subtotal("B","D","F",28,"Total activos no corrientes",act_nct)
    total("B","D","F",38,"TOTAL ACTIVOS",list("BCDEFG"), lambda s: s["total_activo"])

    lineas("I","K","M",pas_cte); subtotal("I","K","M",20,"Total pasivos corrientes",pas_cte)
    ws["I22"].value = "Pasivos no corrientes:"; ws["I22"].font = F(size=13)
    lineas("I","K","M",pas_nct); subtotal("I","K","M",26,"Total pasivos no corrientes",pas_nct)
    total("I","K","M",28,"TOTAL PASIVOS",list("HIJKLMN"), lambda s: s["total_pasivo"])

    ws["I30"].value = "Patrimonio:"; ws["I30"].font = F(size=13)
    for r, clave, lbl in [(31,"capital","  Capital emitido"), (32,"superavit","  Superávit de capital"),
                          (33,"acumulada","  Utilidad acumulada"), (34,"periodo","  Utilidad del periodo"),
                          (35,"reservas","  Reservas")]:
        ws[f"I{r}"].value = lbl; ws[f"I{r}"].font = F(size=13); ws[f"I{r}"].alignment = A("left")
        for col, src in (("K", esf), ("M", esf_ant)):
            if src is None:
                continue
            c = ws[f"{col}{r}"]
            c.value = src["patrimonio"].get(clave, 0) or None
            c.number_format = FMT_COP_XL; c.font = F(size=13)
    total("I","K","M",36,"TOTAL PATRIMONIO",list("HIJKLMN"), lambda s: s["total_patrimonio"])
    total("I","K","M",38,"TOTAL PASIVOS Y PATRIMONIO",list("HIJKLMN"),
          lambda s: s["total_pasivo"] + s["total_patrimonio"])

    ws["B40"].value = "Las notas adjuntas forman parte integral de estos estados financieros."
    ws["B40"].font = F(size=11)


def generar_hoja_eri(ws, empresa, nit, periodo, eri, eri_ant=None, anios=None):
    """eri / eri_ant: resultado de estados.lineas_eri (ingresos +, gastos −).
       eri_ant None → la columna F queda en blanco. anios: (año actual, año anterior)."""
    from openpyxl.styles import PatternFill as _PF
    hay_ant = eri_ant is not None
    eri_azul_osc = _PF("solid", fgColor="1E3A5F")
    eri_azul_med = _PF("solid", fgColor="2E6DA4")
    eri_azul_cla = _PF("solid", fgColor="D6E4F0")

    anchos = {"A":0.9,"B":43.9,"C":6.1,"D":16.6,"E":2.6,"F":16.6,"G":9.0}
    for col, w in anchos.items():
        ws.column_dimensions[col].width = w
    for r in range(1, 35):
        ws.row_dimensions[r].height = 15.0
    for r, h in [(1,30),(2,22),(3,22),(4,20),(5,18),(6,18),(7,18),(8,18)]:
        ws.row_dimensions[r].height = h

    _eri_cols = list("BCDEFG")
    for r, txt, bold, sz in [(1,empresa,True,16),(2,nit,False,13),
                              (3,"ESTADO DE RESULTADOS INTEGRAL",True,15),
                              (4,periodo,False,12),(5,"(En pesos colombianos - $)",False,11)]:
        for col in _eri_cols:
            ws[f"{col}{r}"].fill = eri_azul_osc
        c = ws[f"B{r}"]; c.value = txt
        c.font = Font(bold=bold, size=sz, name="Calibri", color="FFFFFF")

    for col in _eri_cols:
        for r in (6, 7, 8):
            ws[f"{col}{r}"].fill = eri_azul_med
    for col in ("D", "F"):
        c = ws[f"{col}6"]; c.value = "Acumulado"
        c.font = Font(bold=True, size=12, name="Calibri", color="FFFFFF"); c.alignment = A("center")
    c = ws["C7"]; c.value = "NOTA"
    c.font = Font(bold=True, size=11, name="Calibri", color="FFFFFF"); c.alignment = A("center")
    a_act, a_ant = anios if anios else ("", "")
    for col, val in [("D", a_act), ("F", a_ant)]:
        c = ws[f"{col}7"]; c.value = val
        c.font = Font(bold=True, size=11, name="Calibri", color="FFFFFF"); c.alignment = A("center")
    for col in ("D", "F"):
        c = ws[f"{col}8"]; c.value = "$"
        c.font = Font(bold=True, size=11, name="Calibri", color="FFFFFF"); c.alignment = A("center")

    # (fila, etiqueta, nota, clave en lineas_eri, negrita, borde)
    lineas = [
        (10, "Ingresos de actividades ordinarias", 13,   "ing_ord",        False, None),
        (12, "Ganancia bruta",                     None, "ganancia_bruta", True,  None),
        (14, "Otros ingresos",                     14,   "otros_ing",      False, None),
        (15, "Gastos de administración",           15,   "gtos_adm",       False, None),
        (16, "Otros gastos",                       16,   "otros_gto",      False, None),
        (17, "Ingresos financieros",               17,   "ing_fin",        False, None),
        (18, "Gastos financieros",                 16,   "gto_fin",        False, None),
        (21, "Utilidad antes de impuesto",         None, "util_ai",        True,  None),
        (23, "Ingreso (gasto) por impuesto",       19,   "impuesto",       False, None),
        (25, "Utilidad (pérdida) del periodo",     None, "util_per",       True,  None),
        (29, "Resultado integral total",           None, "util_per",       True,  "double"),
    ]
    for row_n, label, nota, clave, bold, border in lineas:
        if bold:
            for col in _eri_cols:
                ws[f"{col}{row_n}"].fill = eri_azul_cla
        color = "1E3A5F" if bold else "000000"
        ws[f"B{row_n}"].value = label
        ws[f"B{row_n}"].font = Font(bold=bold, size=13, name="Calibri", color=color)
        if nota:
            ws[f"C{row_n}"].value = nota; ws[f"C{row_n}"].font = F(size=13)
            ws[f"C{row_n}"].alignment = A("center")
        for col, src in (("D", eri), ("F", eri_ant)):
            if src is None:
                continue
            c = ws[f"{col}{row_n}"]
            c.value = src[clave] or None
            c.number_format = FMT_COP_XL
            c.font = Font(bold=bold, size=13, name="Calibri", color=color)
            if border == "double":
                c.border = Border(bottom=double())

    ws["B31"].value = "Las notas adjuntas forman parte integral de estos estados financieros."
    ws["B31"].font = F(size=12)



def generar_hoja_er_mensualizado(ws, empresa, df_eri_raw):
    """Hoja ER MENSUALIZADO: P&L por mes con detalle de cuentas."""
    from openpyxl.styles import PatternFill, colors
    from openpyxl.utils import get_column_letter

    MESES = [m for m in MESES_ORDEN if m in df_eri_raw["Mes"].unique()]
    MESES_ABR = [MESES_ABREV.get(m, m[:3]) for m in MESES]

    # Pivots por grupo y por cuenta
    df_raw = df_eri_raw.copy()
    df_raw["Cuenta_llave"] = df_raw["Nombre cuenta"].str.strip()

    pivot_grupo = (df_raw.groupby(["Grupo","Mes"])["Saldo Mes"].sum()
                   .unstack(fill_value=0).reindex(columns=MESES, fill_value=0))
    pivot_cuenta = (df_raw.groupby(["Cuenta_llave","Grupo","Mes"])["Saldo Mes"].sum()
                    .unstack(fill_value=0).reindex(columns=MESES, fill_value=0))
    pivot_cuenta = pivot_cuenta.reset_index()

    # Estilos
    azul_osc  = PatternFill("solid", fgColor="1E3A5F")
    azul_med  = PatternFill("solid", fgColor="2E6DA4")
    azul_cla  = PatternFill("solid", fgColor="D6E4F0")
    blanco    = Font(color="FFFFFF", bold=True, size=11, name="Calibri")
    negro_b   = Font(bold=True, size=10, name="Calibri")
    negro_n   = Font(bold=False, size=10, name="Calibri")
    centro    = Alignment(horizontal="center", vertical="center")
    izq       = Alignment(horizontal="left",   vertical="center")

    def fmt_num(ws, cell):
        cell.number_format = '#,##0_);(#,##0);"-"'
        cell.alignment = Alignment(horizontal="right", vertical="center")

    # Anchos
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 42
    for i in range(len(MESES)):
        ws.column_dimensions[get_column_letter(i+3)].width = 16
    ws.column_dimensions[get_column_letter(len(MESES)+3)].width = 18  # ACUMULADO

    # Fila 1 — empresa
    ws.row_dimensions[1].height = 20
    c = ws.cell(1, 2, empresa); c.font = Font(bold=True, size=13, name="Calibri")

    # Fila 2 — título con fondo azul oscuro
    ws.row_dimensions[2].height = 22
    ws.merge_cells(start_row=2, start_column=2, end_row=2,
                   end_column=len(MESES)+3)
    c = ws.cell(2, 2, "ESTADO DE RESULTADOS INTEGRAL  MENSUALIZADO - CONSOLIDADO")
    c.font = blanco; c.fill = azul_osc; c.alignment = centro

    # Fila 4 — cabecera meses
    ws.row_dimensions[4].height = 18
    ws.cell(4, 2, "").font = negro_b
    for i, abr in enumerate(MESES_ABR):
        c = ws.cell(4, i+3, abr.upper() + " ")
        c.font = blanco; c.fill = azul_med; c.alignment = centro
    c = ws.cell(4, len(MESES)+3, "ACUMULADO")
    c.font = blanco; c.fill = azul_med; c.alignment = centro

    # Mapeo grupos → filas del P&L
    # (etiqueta_grupo_en_data, label_display, es_ingreso, es_subtotal_label)
    ESTRUCTURA_PL = [
        # Ingresos
        ("INGRESOS DE ACTIVIDADES ORDINARIAS", "Ingresos de actividades ordinarias", True,  False),
        (None, "VENTAS NETAS",                                                        True,  True),
        (None, "Costo del servicio",                                                  False, False),
        (None, "UTILIDAD BRUTA",                                                      True,  True),
        # Gastos operación
        ("GASTOS DE ADMINISTRACION",          "Gastos Administración",               False, False),
        (None, "GASTOS DE OPERACION",                                                 False, True),
        (None, "UTILIDAD OPERATIVA",                                                  True,  True),
        # Otros
        ("OTROS GASTOS",                      "Otros gastos",                        False, False),
        ("GASTOS FINANCIEROS",                "Gastos financieros",                  False, False),
        ("OTROS INGRESOS",                    "Otros ingresos",                      True,  False),
        (None, "Diferencia en cambio neta",                                           True,  False),
        (None, "UTILIDAD ANTES DE IMPTOS",                                            True,  True),
        ("PROVISION DE IMPUESTOS",            "Provisión impuesto de renta",         False, False),
        (None, "UTILIDAD (PERDIDA) NETA",                                             True,  True),
    ]

    # Precalcular acumulados por grupo
    def gacc(g):
        if g in pivot_grupo.index:
            return {m: pivot_grupo.loc[g, m] for m in MESES}
        return {m: 0 for m in MESES}

    ing_m   = gacc("INGRESOS DE ACTIVIDADES ORDINARIAS")
    gto_m   = gacc("GASTOS DE ADMINISTRACION")
    otrg_m  = gacc("OTROS GASTOS")
    gfin_m  = gacc("GASTOS FINANCIEROS")
    oing_m  = gacc("OTROS INGRESOS")
    prov_m  = gacc("PROVISION DE IMPUESTOS")

    def ub(m):   return ing_m[m]
    def uop(m):  return ing_m[m] - abs(gto_m[m])
    def uai(m):  return uop(m) - abs(otrg_m[m]) - abs(gfin_m[m]) + abs(oing_m[m])
    def unet(m): return uai(m) - abs(prov_m[m])

    subtotales = {
        "VENTAS NETAS":           {m: ing_m[m]  for m in MESES},
        "Costo del servicio":     {m: 0          for m in MESES},
        "UTILIDAD BRUTA":         {m: ub(m)      for m in MESES},
        "GASTOS DE OPERACION":    {m: abs(gto_m[m]) for m in MESES},
        "UTILIDAD OPERATIVA":     {m: uop(m)     for m in MESES},
        "Diferencia en cambio neta": {m: 0        for m in MESES},
        "UTILIDAD ANTES DE IMPTOS":  {m: uai(m)  for m in MESES},
        "UTILIDAD (PERDIDA) NETA":   {m: unet(m) for m in MESES},
    }

    fila = 5
    for grupo_key, label, es_ing, es_sub in ESTRUCTURA_PL:
        ws.row_dimensions[fila].height = 16

        if es_sub:
            # Fila subtotal — fondo azul claro + negrita
            c = ws.cell(fila, 2, label); c.font = negro_b; c.fill = azul_cla
            vals = subtotales.get(label, {m: 0 for m in MESES})
            for i, m in enumerate(MESES):
                cell = ws.cell(fila, i+3, vals[m] if vals[m] != 0 else None)
                cell.fill = azul_cla; fmt_num(ws, cell); cell.font = negro_b
            acum = sum(vals.values())
            cell = ws.cell(fila, len(MESES)+3, acum if acum != 0 else None)
            cell.fill = azul_cla; fmt_num(ws, cell); cell.font = negro_b
            fila += 1

            # Filas de detalle de cuentas del grupo anterior
            if grupo_key is None and es_sub:
                pass  # subtotales sin grupo no tienen detalle
        else:
            if grupo_key and grupo_key in pivot_grupo.index:
                # Fila de grupo (encabezado)
                c = ws.cell(fila, 2, label); c.font = negro_n
                vals = {m: pivot_grupo.loc[grupo_key, m] for m in MESES}
                for i, m in enumerate(MESES):
                    cell = ws.cell(fila, i+3, abs(vals[m]) if vals[m] != 0 else None)
                    fmt_num(ws, cell); cell.font = negro_n
                acum = sum(abs(v) for v in vals.values())
                cell = ws.cell(fila, len(MESES)+3, acum if acum != 0 else None)
                fmt_num(ws, cell); cell.font = negro_n
                fila += 1

                # Cuentas detalle
                cuentas_grp = pivot_cuenta[pivot_cuenta["Grupo"] == grupo_key]
                for _, cr in cuentas_grp.iterrows():
                    ws.row_dimensions[fila].height = 15
                    lbl = "          " + str(cr["Cuenta_llave"])
                    c = ws.cell(fila, 2, lbl); c.font = negro_n; c.alignment = izq
                    for i, m in enumerate(MESES):
                        v = cr[m] if m in cr.index else 0
                        cell = ws.cell(fila, i+3, abs(v) if v != 0 else None)
                        fmt_num(ws, cell); cell.font = negro_n
                    acum_c = sum(abs(cr[m]) for m in MESES if m in cr.index)
                    cell = ws.cell(fila, len(MESES)+3, acum_c if acum_c != 0 else None)
                    fmt_num(ws, cell); cell.font = negro_n
                    fila += 1
            else:
                # Fila sin datos (ej. Costo del servicio, Diferencia en cambio)
                c = ws.cell(fila, 2, label); c.font = negro_n
                for i in range(len(MESES)+1):
                    ws.cell(fila, i+3, None)
                fila += 1

    # Autofilter en fila 4
    ws.auto_filter.ref = f"B4:{get_column_letter(len(MESES)+3)}4"


def generar_hoja_consol(ws, empresa, df_eri_raw):
    """Hoja CONSOL: todos los grupos ERI, detalle de cuentas por mes + ACUMULADO.

    Cubre TODOS los GRUPOS_ERI (no sólo Gastos).
    Columnas: Nombre cuenta | Ene | Feb | ... | ACUMULADO
    ACUMULADO de cada grupo = suma YTD de todas sus cuentas (coincide con ERI).
    """
    from openpyxl.styles import PatternFill
    from openpyxl.utils import get_column_letter

    MESES = [m for m in MESES_ORDEN if m in df_eri_raw["Mes"].unique()]
    MESES_ABR = [MESES_ABREV.get(m, m[:3]).upper() for m in MESES]
    n_mes = len(MESES)
    # total columnas: col A (descripción) + meses + ACUMULADO
    N_COLS = 1 + n_mes + 1

    azul_osc  = PatternFill("solid", fgColor="1E3A5F")
    azul_med  = PatternFill("solid", fgColor="2E6DA4")
    azul_cla  = PatternFill("solid", fgColor="D6E4F0")
    gris_alt  = PatternFill("solid", fgColor="F2F4F7")
    blanco    = Font(color="FFFFFF", bold=True, size=11, name="Calibri")
    negro_b   = Font(bold=True,  size=10, name="Calibri")
    negro_n   = Font(bold=False, size=10, name="Calibri")
    izq       = Alignment(horizontal="left",  vertical="center")
    der       = Alignment(horizontal="right", vertical="center")

    thin_s  = Side(border_style="thin",   color="CCCCCC")
    thick_s = Side(border_style="medium", color="2E6DA4")
    borde_n = Border(left=thin_s,  right=thin_s,  top=thin_s,  bottom=thin_s)
    borde_g = Border(left=thick_s, right=thick_s, top=thick_s, bottom=thick_s)

    def fmt_num(cell, bold=False):
        cell.number_format = FMT_COP_XL
        cell.alignment = der
        cell.font = negro_b if bold else negro_n

    # Anchos de columna
    ws.column_dimensions["A"].width = 50
    for j in range(2, N_COLS):
        ws.column_dimensions[get_column_letter(j)].width = 15
    ws.column_dimensions[get_column_letter(N_COLS)].width = 18  # ACUMULADO

    # Fila 1: título fusionado
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=N_COLS)
    c = ws.cell(1, 1, f"CONSOLIDADO ESTADO DE RESULTADOS — {empresa}")
    c.font = blanco; c.fill = azul_osc
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 22

    # Fila 2: encabezados
    ws.row_dimensions[2].height = 18
    c = ws.cell(2, 1, "Grupo / Cuenta"); c.font = blanco; c.fill = azul_med
    c.alignment = Alignment(horizontal="center", vertical="center")
    for j, abr in enumerate(MESES_ABR, 2):
        c = ws.cell(2, j, abr); c.font = blanco; c.fill = azul_med
        c.alignment = Alignment(horizontal="center", vertical="center")
    c = ws.cell(2, N_COLS, "ACUMULADO"); c.font = blanco; c.fill = azul_med
    c.alignment = Alignment(horizontal="center", vertical="center")

    # Preparar pivot por cuenta × mes
    df_raw = df_eri_raw.copy()
    df_raw["_cuenta"] = df_raw["Nombre cuenta"].str.strip()
    pivot_cta = (df_raw.groupby(["_cuenta", "Grupo", "Mes"])["Saldo Mes"].sum()
                 .unstack(fill_value=0).reindex(columns=MESES, fill_value=0)
                 .reset_index())

    # Mapeo grupo → (etiqueta sección, etiqueta total)
    LABEL_GRUPO = {
        "INGRESOS DE ACTIVIDADES ORDINARIAS": ("INGRESOS DE ACTIVIDADES ORDINARIAS",  "TOTAL INGRESOS ORDINARIOS"),
        "OTROS INGRESOS":                     ("OTROS INGRESOS",                      "TOTAL OTROS INGRESOS"),
        "GASTOS DE ADMINISTRACION":           ("GASTOS DE ADMINISTRACIÓN",            "TOTAL GASTOS DE ADMINISTRACIÓN"),
        "OTROS GASTOS":                       ("OTROS GASTOS",                        "TOTAL OTROS GASTOS"),
        "INGRESOS FINANCIEROS":               ("INGRESOS FINANCIEROS",                "TOTAL INGRESOS FINANCIEROS"),
        "GASTOS FINANCIEROS":                 ("GASTOS NO OPERACIONALES",             "TOTAL GASTOS NO OPERACIONALES"),
        "PROVISION DE IMPUESTOS":             ("PROVISIÓN DE IMPUESTOS",              "TOTAL PROVISIÓN DE IMPUESTOS"),
    }

    fila = 3
    totales_gran_mes = {m: 0.0 for m in MESES}

    for grupo_key in GRUPOS_ERI:
        cuentas_grp = pivot_cta[pivot_cta["Grupo"] == grupo_key]
        if cuentas_grp.empty:
            continue

        titulo_secc, titulo_total = LABEL_GRUPO.get(grupo_key, (grupo_key, f"TOTAL {grupo_key}"))

        # Fila encabezado de grupo
        ws.row_dimensions[fila].height = 16
        c = ws.cell(fila, 1, titulo_secc)
        c.font = negro_b; c.fill = azul_cla; c.alignment = izq; c.border = borde_g
        for j in range(2, N_COLS + 1):
            cell = ws.cell(fila, j); cell.fill = azul_cla; cell.border = borde_n
        fila += 1

        totales_sec_mes = {m: 0.0 for m in MESES}

        for ri, (_, cr) in enumerate(cuentas_grp.iterrows()):
            ws.row_dimensions[fila].height = 15
            lbl = str(cr["_cuenta"])
            fill_row = gris_alt if ri % 2 == 0 else None

            c = ws.cell(fila, 1, "  " + lbl)
            c.font = negro_n; c.alignment = izq; c.border = borde_n
            if fill_row: c.fill = fill_row

            row_acum = 0.0
            for j, m in enumerate(MESES, 2):
                v = abs(float(cr[m])) if m in cr.index else 0.0
                totales_sec_mes[m] += v
                cell = ws.cell(fila, j, v if v != 0 else None)
                fmt_num(cell); cell.border = borde_n
                if fill_row: cell.fill = fill_row
                row_acum += v

            cell = ws.cell(fila, N_COLS, row_acum if row_acum != 0 else None)
            fmt_num(cell); cell.border = borde_n
            if fill_row: cell.fill = fill_row
            fila += 1

        # Fila total de sección
        ws.row_dimensions[fila].height = 16
        c = ws.cell(fila, 1, titulo_total)
        c.font = negro_b; c.fill = azul_cla; c.alignment = izq; c.border = borde_g
        sec_acum = 0.0
        for j, m in enumerate(MESES, 2):
            v = totales_sec_mes[m]
            totales_gran_mes[m] += v
            cell = ws.cell(fila, j, v if v != 0 else None)
            fmt_num(cell, bold=True); cell.fill = azul_cla; cell.border = borde_n
            sec_acum += v
        cell = ws.cell(fila, N_COLS, sec_acum if sec_acum != 0 else None)
        fmt_num(cell, bold=True); cell.fill = azul_cla; cell.border = borde_n
        fila += 1

        # Espacio entre secciones
        ws.row_dimensions[fila].height = 6
        fila += 1

    # Fila gran total
    ws.row_dimensions[fila].height = 18
    c = ws.cell(fila, 1, "TOTAL GENERAL")
    c.font = Font(bold=True, size=11, color="FFFFFF", name="Calibri"); c.fill = azul_osc
    c.alignment = izq
    gt_acum = 0.0
    for j, m in enumerate(MESES, 2):
        v = totales_gran_mes[m]
        cell = ws.cell(fila, j, v if v != 0 else None)
        cell.number_format = FMT_COP_XL; cell.alignment = der
        cell.font = Font(bold=True, size=11, color="FFFFFF", name="Calibri")
        cell.fill = azul_osc
        gt_acum += v
    cell = ws.cell(fila, N_COLS, gt_acum if gt_acum != 0 else None)
    cell.number_format = FMT_COP_XL; cell.alignment = der
    cell.font = Font(bold=True, size=11, color="FFFFFF", name="Calibri")
    cell.fill = azul_osc

    ws.freeze_panes = "B3"


def _escribir_df_en_hoja(ws, df, index=True):
    """Escribe un DataFrame en un Worksheet de openpyxl sin pandas ExcelWriter."""
    from openpyxl.utils import get_column_letter
    if index:
        ws.append([""] + list(df.columns))
        for row_idx, (idx_val, row) in enumerate(df.iterrows()):
            ws.append([str(idx_val)] + [
                float(v) if isinstance(v, (int, float)) and not pd.isna(v) else str(v)
                for v in row
            ])
    else:
        ws.append(list(df.columns))
        for _, row in df.iterrows():
            ws.append([
                float(v) if isinstance(v, (int, float)) and not pd.isna(v) else str(v)
                for v in row
            ])


def generar_hoja_anexo(ws, df_raw_src, titulo, es_pivot=True, grupos_orden=None):
    """Formatea una hoja de Anexo con jerarquía Grupo → Cuenta → Tercero por mes.

    es_pivot=True  → expansión jerárquica: Grupo (subtotal) > Cuenta > Tercero
    es_pivot=False → tabla de detalle plano (Codigo, Nombre cuenta, Nit, Nombre tercero, Mes, Saldo Mes…)
    """
    from openpyxl.styles import PatternFill
    from openpyxl.utils import get_column_letter

    azul_osc  = PatternFill("solid", fgColor="1E3A5F")
    azul_med  = PatternFill("solid", fgColor="2E6DA4")
    azul_cla  = PatternFill("solid", fgColor="D6E4F0")
    gris_alt  = PatternFill("solid", fgColor="F2F4F7")

    blanco    = Font(color="FFFFFF", bold=True, size=11, name="Calibri")
    negro_b   = Font(bold=True,  size=10, name="Calibri")
    negro_n   = Font(bold=False, size=10, name="Calibri")
    negro_it  = Font(bold=False, size=9,  name="Calibri", italic=True, color="444444")
    centro    = Alignment(horizontal="center", vertical="center", wrap_text=True)
    izq       = Alignment(horizontal="left",   vertical="center", wrap_text=False)
    der       = Alignment(horizontal="right",  vertical="center")

    thin_s  = Side(border_style="thin",   color="CCCCCC")
    thick_s = Side(border_style="medium", color="2E6DA4")
    borde_n = Border(left=thin_s, right=thin_s, top=thin_s, bottom=thin_s)
    borde_g = Border(left=thick_s, right=thin_s, top=thick_s, bottom=thick_s)  # grupos

    def fmt_num(cell, bold=False):
        cell.number_format = FMT_COP_XL
        cell.alignment = der
        cell.font = negro_b if bold else negro_n

    # ────────────────────────────────────────────────────────────────────────────
    if es_pivot:
        # Pivot jerárquico: Grupo → Cuenta → Tercero × Meses
        df = df_raw_src.copy()
        MESES = [m for m in MESES_ORDEN if m in df["Mes"].unique()]
        n_mes = len(MESES)
        n_cols = 1 + n_mes + 1   # col Descripción + meses + Total general

        # Anchos
        ws.column_dimensions["A"].width = 52
        for j in range(2, n_cols + 1):
            ws.column_dimensions[get_column_letter(j)].width = 20 if j == n_cols else 15

        # Fila 1: título
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
        c = ws.cell(1, 1, titulo); c.font = blanco; c.fill = azul_osc
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 22

        # Fila 2: encabezados
        ws.row_dimensions[2].height = 18
        c = ws.cell(2, 1, "Grupo / Cuenta / Tercero"); c.font = blanco; c.fill = azul_med; c.alignment = centro
        for j, m in enumerate(MESES, 2):
            c = ws.cell(2, j, MESES_ABREV.get(m, m[:3]).upper())
            c.font = blanco; c.fill = azul_med; c.alignment = centro
        c = ws.cell(2, n_cols, "TOTAL"); c.font = blanco; c.fill = azul_med; c.alignment = centro

        # Pivot base: Grupo × Mes
        piv_grp = (df.groupby(["Grupo", "Mes"])["Saldo Mes"].sum()
                   .unstack(fill_value=0).reindex(columns=MESES, fill_value=0))
        # Pivot cuenta: Cuenta × Mes (clave = Nombre cuenta)
        df["_cuenta"] = df["Nombre cuenta"].str.strip()
        piv_cta = (df.groupby(["_cuenta", "Grupo", "Mes"])["Saldo Mes"].sum()
                   .unstack(fill_value=0).reindex(columns=MESES, fill_value=0).reset_index())
        # Pivot tercero: Tercero × Mes (clave = Nit + Nombre tercero)
        df["_tercero"] = df["Nit"].astype(str).str.strip() + "  " + df["Nombre tercero"].fillna("").str.strip()
        piv_ter = (df.groupby(["_tercero", "_cuenta", "Grupo", "Mes"])["Saldo Mes"].sum()
                   .unstack(fill_value=0).reindex(columns=MESES, fill_value=0).reset_index())

        orden_grp = grupos_orden if grupos_orden else list(piv_grp.index)

        # Esquema de Excel: el botón +/− queda en la fila del grupo o de la cuenta (arriba del detalle)
        ws.sheet_properties.outlinePr.summaryBelow = False

        fila = 3
        for grp in orden_grp:
            if grp not in piv_grp.index:
                continue
            # ── Fila grupo (subtotal) ──
            ws.row_dimensions[fila].height = 16
            c = ws.cell(fila, 1, grp); c.font = negro_b; c.fill = azul_cla; c.alignment = izq; c.border = borde_g
            vals_g = [piv_grp.loc[grp, m] for m in MESES]
            tot_g = sum(abs(v) for v in vals_g)
            for j, v in enumerate(vals_g, 2):
                cell = ws.cell(fila, j, abs(v) if v != 0 else None)
                fmt_num(cell, bold=True); cell.fill = azul_cla; cell.border = borde_n
            cell = ws.cell(fila, n_cols, tot_g if tot_g != 0 else None)
            fmt_num(cell, bold=True); cell.fill = azul_cla; cell.border = borde_n
            ws.row_dimensions[fila].collapsed = True
            fila += 1

            # ── Filas de cuentas dentro del grupo ──
            ctas = piv_cta[piv_cta["Grupo"] == grp]
            for _, cr in ctas.iterrows():
                cta_lbl = str(cr["_cuenta"])
                vals_c = [cr[m] if m in cr.index else 0 for m in MESES]
                tot_c  = sum(abs(v) for v in vals_c)

                ws.row_dimensions[fila].height = 15
                c = ws.cell(fila, 1, "  " + cta_lbl); c.font = negro_n; c.alignment = izq; c.border = borde_n
                for j, v in enumerate(vals_c, 2):
                    cell = ws.cell(fila, j, abs(v) if v != 0 else None)
                    fmt_num(cell); cell.border = borde_n
                cell = ws.cell(fila, n_cols, tot_c if tot_c != 0 else None)
                fmt_num(cell); cell.border = borde_n
                ws.row_dimensions[fila].outlineLevel = 1      # cuenta: nivel 1, contraída
                ws.row_dimensions[fila].hidden = True
                ws.row_dimensions[fila].collapsed = True
                fila += 1

                # ── Filas de terceros dentro de la cuenta ──
                terceros = piv_ter[(piv_ter["Grupo"] == grp) & (piv_ter["_cuenta"] == cta_lbl)]
                for _, tr in terceros.iterrows():
                    ter_lbl = str(tr["_tercero"])
                    if ter_lbl.strip() in ("", "nan  ", "  "):
                        continue
                    vals_t = [tr[m] if m in tr.index else 0 for m in MESES]
                    tot_t  = sum(abs(v) for v in vals_t)
                    ws.row_dimensions[fila].height = 14
                    fill_t = gris_alt if fila % 2 == 0 else None
                    c = ws.cell(fila, 1, "      " + ter_lbl); c.font = negro_it; c.alignment = izq; c.border = borde_n
                    if fill_t: c.fill = fill_t
                    for j, v in enumerate(vals_t, 2):
                        cell = ws.cell(fila, j, abs(v) if v != 0 else None)
                        fmt_num(cell); cell.border = borde_n
                        if fill_t: cell.fill = fill_t
                    cell = ws.cell(fila, n_cols, tot_t if tot_t != 0 else None)
                    fmt_num(cell); cell.border = borde_n
                    if fill_t: cell.fill = fill_t
                    ws.row_dimensions[fila].outlineLevel = 2  # tercero: nivel 2, contraído
                    ws.row_dimensions[fila].hidden = True
                    fila += 1

        ws.freeze_panes = "B3"

    # ────────────────────────────────────────────────────────────────────────────
    else:
        # Tabla de detalle plano — sin columna Codigo ni Cuenta
        df = df_raw_src.copy()
        for _col_drop in ("Codigo", "Cuenta"):
            if _col_drop in df.columns:
                df = df.drop(columns=[_col_drop])
        columnas = list(df.columns)
        n_cols   = len(columnas)

        # Fila 1: título fusionado
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
        c = ws.cell(1, 1, titulo); c.font = blanco; c.fill = azul_osc
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 22

        # Fila 2: encabezados
        ws.row_dimensions[2].height = 18
        for j, col in enumerate(columnas, 1):
            c = ws.cell(2, j, col); c.font = blanco; c.fill = azul_med; c.alignment = centro

        # Anchos por columna
        anchos_det = {
            "Codigo": 12, "Nombre cuenta": 36, "Nit": 15,
            "Nombre tercero": 36, "Mes": 14, "Saldo Mes": 18,
            "Cuenta": 12, "Grupo": 46,
        }
        for j, col in enumerate(columnas, 1):
            ws.column_dimensions[get_column_letter(j)].width = anchos_det.get(col, 16)

        # Filas de datos
        for i, (_, row) in enumerate(df.iterrows(), 3):
            ws.row_dimensions[i].height = 14
            fill = gris_alt if i % 2 == 0 else None

            for j, col in enumerate(columnas, 1):
                val = row[col]
                c = ws.cell(i, j)
                if col == "Saldo Mes":
                    c.value = float(val) if not pd.isna(val) else None
                    c.number_format = FMT_COP_XL; c.alignment = der
                elif col == "Mes":
                    c.value = str(val) if val is not None else ""; c.alignment = centro
                elif col in ("Codigo", "Nit", "Cuenta"):
                    c.value = str(val) if val is not None else ""; c.alignment = centro
                else:
                    c.value = str(val) if val is not None else ""; c.alignment = izq
                c.font = negro_n
                if fill: c.fill = fill
                c.border = borde_n

        ws.freeze_panes = "A3"
        ws.auto_filter.ref = f"A2:{get_column_letter(n_cols)}2"


def generar_excel_eeff(empresa, nit, periodo, esf, eri, pivot_eri, df_eri_raw, df_esf_raw,
                       esf_ant=None, eri_ant=None, fechas=None, anios=None):
    """esf/eri: resultados de estados.lineas_esf / lineas_eri (con signo de presentación).
       esf_ant/eri_ant: período anterior o None. Hojas en el orden del modelo EEFF."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    generar_hoja_esf(wb.create_sheet("ESF"), empresa, nit, periodo, esf, esf_ant, fechas)
    generar_hoja_anexo(wb.create_sheet("ANEXO ESF"), df_esf_raw,
                       titulo="ANEXO ESF — SALDOS MENSUALES POR GRUPO", es_pivot=True,
                       grupos_orden=GRUPOS_ESF_ORDEN)
    generar_hoja_eri(wb.create_sheet("ERI"), empresa, nit, periodo, eri, eri_ant, anios)
    generar_hoja_anexo(wb.create_sheet("ANEXO ERI"), df_eri_raw,
                       titulo="ANEXO ERI — MOVIMIENTOS MENSUALES POR GRUPO", es_pivot=True,
                       grupos_orden=GRUPOS_ERI)
    generar_hoja_er_mensualizado(wb.create_sheet("ER MENSUALIZADO"), empresa, df_eri_raw)
    generar_hoja_consol(wb.create_sheet("CONSOL"), empresa, df_eri_raw)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@st.cache_data(show_spinner=False)
def excel_eeff_en_bytes(empresa, nit, periodo, esf, eri, pivot_eri, df_eri_raw, df_esf_raw,
                        esf_ant, eri_ant, fechas, anios):
    """Genera el Excel una sola vez por combinación de datos y opciones (queda en caché)."""
    return generar_excel_eeff(empresa, nit, periodo, esf, eri, pivot_eri, df_eri_raw, df_esf_raw,
                              esf_ant=esf_ant, eri_ant=eri_ant, fechas=fechas, anios=anios).getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════
page_header('Anexos EEFF – ERI y ESF', 'Genera los estados financieros formateados (ESF y ERI) desde la hoja <strong>terceros_</strong>', 'bar-chart')

md('<p class="section-title">[[folder]] Archivo Excel de Anexos EEFF</p>', unsafe_allow_html=True)
st.caption("Debe contener la hoja **terceros_** con columnas: Codigo, Nombre cuenta, Nit, Nombre tercero, Mes, Saldo Mes, Cuenta, Grupo")
uploaded = st.file_uploader("Sube el archivo Excel", type=["xlsx"], label_visibility="collapsed")

if not uploaded:
    empty_state('Sube el archivo Excel para generar los estados financieros', '')
    st.stop()

file_bytes = uploaded.read()
res = procesar_archivo(file_bytes)

if res["errores"]:
    st.error(":material/cancel: El archivo no se puede procesar. Corrige estos puntos y vuelve a subirlo:")
    st.dataframe(pd.DataFrame(res["errores"]).rename(
        columns={"fila": "Fila (Excel)", "columna": "Columna", "motivo": "Motivo"}),
        use_container_width=True, hide_index=True)
    st.stop()

df_eri_raw, pivot_eri = res["df_eri_raw"], res["pivot_eri"]
df_esf_raw, pivot_esf = res["df_esf_raw"], res["pivot_esf"]
ultimo_mes = res["ultimo_mes"]
if not ultimo_mes:
    st.error(":material/cancel: El archivo no tiene saldos de balance (ESF) en ningún mes."); st.stop()

if res["avisos"]:
    with st.expander(f":material/warning: {len(res['avisos'])} aviso(s) sobre el archivo", expanded=True):
        st.dataframe(pd.DataFrame(res["avisos"]).rename(
            columns={"fila": "Fila (Excel)", "columna": "Columna", "motivo": "Motivo"}),
            use_container_width=True, hide_index=True)

meses_disp     = [m for m in MESES_ORDEN if m in pivot_eri.columns]
meses_disp_esf = [m for m in MESES_ORDEN if m in pivot_esf.columns]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    md("""<div style="background:linear-gradient(135deg,#1E3A5F,#2E6DA4);padding:14px 18px;
                border-radius:10px;margin-bottom:16px;color:white;text-align:center;">
        <div style="font-size:1.1rem;font-weight:700;">[[building]] Datos de la empresa</div></div>""",
        unsafe_allow_html=True)
    empresa = st.text_input("Nombre empresa", value="MI EMPRESA S.A.S")
    nit     = st.text_input("NIT", value="NIT 000.000.000-0")
    meses_esf_op = [m for m in MESES_ORDEN if m in pivot_esf.columns]
    mes_corte = st.selectbox("Mes de corte", meses_esf_op, index=len(meses_esf_op) - 1,
                             format_func=str.title,
                             help="Mes con el que se arma el ESF (saldo de cierre) y hasta el que se acumula el ERI.")
    anio = st.number_input("Año del período", min_value=2000, max_value=2100,
                           value=datetime.date.today().year - 1, step=1)
    anio = int(anio)
    periodo = st.text_input("Período (texto del encabezado)", value=E.texto_periodo(mes_corte, anio),
                            key=f"periodo_{mes_corte}_{anio}")
    tolerancia = st.number_input("Tolerancia de las validaciones ($)", min_value=0.0, value=2.0, step=1.0,
                                 help="Diferencias hasta este valor se consideran cuadradas (redondeos).")

    st.divider()
    md("**:material/tune: Filtros**")
    todos_meses = st.toggle("Todos los meses", value=True, key="tog_meses")
    if todos_meses:
        meses_sel = meses_disp
    else:
        meses_sel = []
        filas = [meses_disp[i:i+4] for i in range(0, len(meses_disp), 4)]
        for fila in filas:
            cols_sb = st.columns(len(fila))
            for col_sb, mes in zip(cols_sb, fila):
                if col_sb.checkbox(MESES_ABREV[mes], value=True, key=f"m_{mes}"):
                    meses_sel.append(mes)

if not meses_sel:
    st.warning("Selecciona al menos un mes."); st.stop()

# ── Tabs principales ──────────────────────────────────────────────────────────
# ── Cálculo de los estados al mes de corte ────────────────────────────────────
eri_act, esf_act = calcular_estados(res, mes_corte)
validaciones = E.validar_totales(res["base"], mes_corte, esf_act, eri_act, tolerancia)
descuadres = calcular_descuadres(res["base"], tolerancia, mes_corte)
hay_dif = any(v["estado"] == "Diferencia" for v in validaciones)
if hay_dif:
    st.warning(":material/warning: Hay totales que no cuadran contra el Anexo. Revisa la pestaña **Validaciones** "
               "antes de usar el archivo generado.")
else:
    st.success(":material/check_circle: Los totales de activos, pasivos, patrimonio y resultado cuadran con el Anexo.")

tab_eri, tab_esf, tab_val, tab_exportar = st.tabs([
    ":material/trending_up: Estado de Resultados (ERI)",
    ":material/account_balance: Estado de Situación Financiera (ESF)",
    ":material/fact_check: Validaciones",
    ":material/description: Exportar EEFF Formateado",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB ERI
# ══════════════════════════════════════════════════════════════════════════════
with tab_eri:
    cols_eri  = meses_sel + ["Total general"]
    pivot_f   = pivot_eri.loc[
        [g for g in GRUPOS_ERI if g in pivot_eri.index] + ["Total general"], cols_eri]

    ingresos = pivot_f.loc[
        [g for g in ["INGRESOS DE ACTIVIDADES ORDINARIAS","OTROS INGRESOS","INGRESOS FINANCIEROS"]
         if g in pivot_f.index], "Total general"].sum()
    gastos   = pivot_f.loc[
        [g for g in ["GASTOS DE ADMINISTRACION","OTROS GASTOS","GASTOS FINANCIEROS","PROVISION DE IMPUESTOS"]
         if g in pivot_f.index], "Total general"].sum()
    resultado = ingresos + gastos

    md("---")
    m1, m2, m3 = st.columns(3)
    with m1:
        md(f"""<div class="metric-card"><div class="number green">{fmt_cop(abs(ingresos))}</div>
            <div class="label">Total Ingresos</div></div>""", unsafe_allow_html=True)
    with m2:
        md(f"""<div class="metric-card"><div class="number red">{fmt_cop(gastos)}</div>
            <div class="label">Total Gastos</div></div>""", unsafe_allow_html=True)
    with m3:
        rc = "green" if resultado < 0 else "red"
        rl = "Utilidad" if resultado < 0 else "Pérdida"
        md(f"""<div class="metric-card"><div class="number {rc}">{fmt_cop(abs(resultado))}</div>
            <div class="label">Resultado · {rl}</div></div>""", unsafe_allow_html=True)

    md("---")
    md('<p class="section-title">[[clipboard-list]] Resumen ERI por Grupo y Mes</p>', unsafe_allow_html=True)
    st.dataframe(pivot_f.style.format(fmt_cop), use_container_width=True,
                 height=min(60+40*len(pivot_f), 500))
    md("---")

    gt1, gt2, gt3 = st.tabs([":material/trending_up: Evolución mensual",":material/pie_chart: Composición",":material/search: Detalle por tercero"])
    with gt1:
        fig = go.Figure()
        for grupo in [g for g in GRUPOS_ERI if g in pivot_f.index]:
            vals = [pivot_f.loc[grupo, m] if m in pivot_f.columns else 0 for m in meses_sel]
            fig.add_trace(go.Bar(name=grupo, x=meses_sel, y=[abs(v) for v in vals],
                marker_color=COLORES_ERI.get(grupo,"#95a5a6"),
                customdata=[fmt_cop(v) for v in vals],
                hovertemplate=f"<b>{grupo}</b><br>%{{x}}: %{{customdata}}<extra></extra>"))
        fig.update_layout(barmode="group", title="Evolución mensual por grupo",
            xaxis_title="Mes", yaxis_title="COP", height=420,
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with gt2:
        tot_pie = pivot_f.loc[[g for g in GRUPOS_ERI if g in pivot_f.index],"Total general"]
        fig2 = px.pie(values=tot_pie.abs().values, names=tot_pie.index,
            title="Composición por grupo", color=tot_pie.index,
            color_discrete_map=COLORES_ERI, hole=0.4)
        fig2.update_traces(textposition="outside", textinfo="percent+label")
        fig2.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    with gt3:
        gd = st.selectbox("Grupo", GRUPOS_ERI, key="eri_det_g")
        mes_det = st.selectbox("Mes",   ["Todos"]+meses_sel, key="eri_det_m")
        mask = df_eri_raw["Grupo"] == gd
        if mes_det != "Todos": mask &= df_eri_raw["Mes"] == mes_det
        df_d = (df_eri_raw[mask & df_eri_raw["Nombre tercero"].notna()]
            [["Mes","Nombre cuenta","Nit","Nombre tercero","Saldo Mes"]]
            .sort_values("Saldo Mes", key=abs, ascending=False).reset_index(drop=True))
        df_d["Saldo Mes"] = df_d["Saldo Mes"].apply(fmt_cop)
        st.dataframe(df_d, use_container_width=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# TAB ESF
# ══════════════════════════════════════════════════════════════════════════════
with tab_esf:
    act_r = [g for g in GRUPOS_ESF_ACTIVO if g in pivot_esf.index]
    pas_r = [g for g in GRUPOS_ESF_PASIVO if g in pivot_esf.index]
    meses_esf_f = [m for m in meses_disp_esf if m in meses_sel] or meses_disp_esf
    cols_esf_f  = meses_esf_f

    md("---")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        md(f"""<div class="metric-card"><div class="number green">{fmt_cop(esf_act["total_activo"])}</div>
            <div class="label">Total Activo ({mes_corte.title()})</div></div>""", unsafe_allow_html=True)
    with mc2:
        md(f"""<div class="metric-card"><div class="number red">{fmt_cop(esf_act["total_pasivo"])}</div>
            <div class="label">Total Pasivo ({mes_corte.title()})</div></div>""", unsafe_allow_html=True)
    with mc3:
        md(f"""<div class="metric-card"><div class="number blue">{fmt_cop(esf_act["total_patrimonio"])}</div>
            <div class="label">Patrimonio ({mes_corte.title()})</div></div>""", unsafe_allow_html=True)
    st.caption("El ESF muestra el saldo de cierre de cada mes; por eso no hay un «total general» que sume los meses.")

    md("---")
    md('<p class="section-title">[[clipboard-list]] ESF por Grupo y Mes</p>', unsafe_allow_html=True)
    frames = []
    if act_r: frames.append(pivot_esf.loc[act_r, cols_esf_f])
    if "Total Activo" in pivot_esf.index: frames.append(pivot_esf.loc[["Total Activo"], cols_esf_f])
    if pas_r: frames.append(pivot_esf.loc[pas_r, cols_esf_f])
    if "Total Pasivo" in pivot_esf.index: frames.append(pivot_esf.loc[["Total Pasivo"], cols_esf_f])
    pivot_esf_f = pd.concat(frames) if frames else pd.DataFrame()

    def style_esf(row):
        if row.name in ("Total Activo","Total Pasivo"):
            return ["font-weight:bold;background-color:rgba(46, 109, 164, .18)"]*len(row)
        if row.name in GRUPOS_ESF_ACTIVO: return ["color:#1A9E5C"]*len(row)
        return ["color:#D63B3B"]*len(row)

    st.dataframe(pivot_esf_f.style.format(fmt_cop).apply(style_esf, axis=1),
                 use_container_width=True, height=min(60+40*len(pivot_esf_f), 600))
    md("---")

    et1, et2, et3 = st.tabs([":material/bar_chart: Activo vs Pasivo mensual",":material/pie_chart: Composición ESF",":material/search: Detalle por tercero"])
    with et1:
        a_v = [pivot_esf.loc[act_r, m].sum() if act_r and m in pivot_esf.columns else 0 for m in meses_disp_esf]
        p_v = [pivot_esf.loc[pas_r, m].sum() if pas_r and m in pivot_esf.columns else 0 for m in meses_disp_esf]
        fig_e1 = go.Figure()
        fig_e1.add_trace(go.Scatter(x=meses_disp_esf, y=a_v, mode="lines+markers", name="Total Activo",
            line=dict(color="#1A9E5C",width=3), customdata=[fmt_cop(v) for v in a_v],
            hovertemplate="<b>Activo</b><br>%{x}: %{customdata}<extra></extra>"))
        fig_e1.add_trace(go.Scatter(x=meses_disp_esf, y=p_v, mode="lines+markers", name="Total Pasivo",
            line=dict(color="#D63B3B",width=3), customdata=[fmt_cop(v) for v in p_v],
            hovertemplate="<b>Pasivo</b><br>%{x}: %{customdata}<extra></extra>"))
        fig_e1.update_layout(title="Evolución mensual Activo vs Pasivo",
            xaxis_title="Mes", yaxis_title="COP", height=420,
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_e1, use_container_width=True)
    with et2:
        grupos_pie = [g for g in GRUPOS_ESF_ORDEN if g in pivot_esf_f.index]
        tot_pie_e = pivot_esf_f.loc[grupos_pie, mes_corte].abs() if mes_corte in pivot_esf_f.columns else pivot_esf_f.loc[grupos_pie].iloc[:, -1].abs()
        fig_e2 = go.Figure(go.Pie(
            labels=[GRUPOS_LABEL_ESF.get(g,g) for g in tot_pie_e.index],
            values=tot_pie_e.values,
            marker_colors=[COLORES_ESF.get(g,"#aaa") for g in tot_pie_e.index],
            hole=0.4, textposition="outside", textinfo="percent+label"))
        fig_e2.update_layout(title=f"Composición ESF ({mes_corte.title()})", height=500, showlegend=False)
        st.plotly_chart(fig_e2, use_container_width=True)
    with et3:
        opc = [g for g in GRUPOS_ESF_ORDEN if g in df_esf_raw["Grupo"].unique()]
        gde = st.selectbox("Grupo ESF", opc, key="esf_det_g")
        mde = st.selectbox("Mes",   ["Todos"]+meses_disp_esf, key="esf_det_m")
        mask_e = df_esf_raw["Grupo"] == gde
        if mde != "Todos": mask_e &= df_esf_raw["Mes"] == mde
        df_de = (df_esf_raw[mask_e & df_esf_raw["Nombre tercero"].notna()]
            [["Mes","Nombre cuenta","Nit","Nombre tercero","Saldo Mes"]]
            .sort_values("Saldo Mes", key=abs, ascending=False).reset_index(drop=True))
        df_de["Saldo Mes"] = df_de["Saldo Mes"].apply(fmt_cop)
        st.dataframe(df_de, use_container_width=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# TAB VALIDACIONES
# ══════════════════════════════════════════════════════════════════════════════
with tab_val:
    md("---")
    md('<p class="section-title">[[clipboard-list]] Totales contra el Anexo</p>', unsafe_allow_html=True)
    st.caption(f"Corte: {mes_corte.title()} de {anio}. Cada control compara lo que calcula el programa con el total "
               f"que trae el propio Anexo. Tolerancia: $ {tolerancia:,.0f}.")
    tabla = pd.DataFrame(validaciones).rename(columns={
        "control": "Control", "calculado": "Calculado", "anexo": "Según el Anexo",
        "diferencia": "Diferencia", "estado": "Estado", "nota": "Qué significa"})
    for col in ("Calculado", "Según el Anexo", "Diferencia"):
        tabla[col] = tabla[col].apply(lambda x: "-" if x is None or pd.isna(x) else f"{x:,.2f}")
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    md('<p class="section-title">[[search]] Totales que no coinciden con su detalle</p>', unsafe_allow_html=True)
    st.caption("Cuentas cuyo total en el Anexo es distinto de la suma de sus subcuentas y terceros. "
               "Es un problema del archivo de origen, no del programa: suele explicar las diferencias de arriba.")
    if descuadres.empty:
        st.success(":material/check_circle: Todos los totales coinciden con la suma de su detalle.")
    else:
        solo_corte = st.toggle("Mostrar solo lo que afecta al corte seleccionado (ERI y ESF del corte)",
                               value=True, key="solo_corte")
        d = descuadres[descuadres["Afecta"].isin(["ERI", "ESF del corte"])] if solo_corte else descuadres
        st.dataframe(d.style.format({"Total en el Anexo": "{:,.2f}", "Suma del detalle": "{:,.2f}",
                                     "Diferencia": "{:,.2f}"}),
                     use_container_width=True, hide_index=True, height=min(60 + 36 * len(d), 450))

# ══════════════════════════════════════════════════════════════════════════════
# TAB EXPORTAR EEFF FORMATEADO
# ══════════════════════════════════════════════════════════════════════════════
with tab_exportar:
    md("---")
    md('<p class="section-title">[[file-text]] Generar EEFF con formato profesional</p>', unsafe_allow_html=True)
    st.info(
        "Genera un archivo Excel con las hojas del modelo: **ESF, ANEXO ESF, ERI, ANEXO ERI, "
        "ER MENSUALIZADO y CONSOL**. Configura la empresa, el mes de corte y el año en el panel lateral."
    )

    # ── Período anterior ─────────────────────────────────────────────────────
    # Opción 1: detectado automáticamente en el mismo archivo (mes "PERIODO ANTERIOR")
    # Opción 2: archivo separado del año anterior
    eri_ant = esf_ant = None
    if res["ant_auto"]:
        eri_ant, esf_ant = calcular_anterior_auto(res["ant_auto"])
        st.success(":material/check_circle: Período anterior detectado en el mismo archivo (fila con Mes = 'PERIODO ANTERIOR')")
    else:
        md("**:material/folder_open: Archivo del período anterior** *(opcional)*")
        uploaded_ant = st.file_uploader(
            "Sube el archivo Excel del año anterior (misma estructura, hoja 'terceros_')",
            type=["xlsx"],
            key="uploader_anterior",
        )
        if uploaded_ant is not None:
            # Guardar bytes en session_state para que sobrevivan reruns
            st.session_state["_ant_bytes"] = uploaded_ant.read()
            st.session_state["_ant_name"]  = uploaded_ant.name

        if "_ant_bytes" in st.session_state:
            res_ant = procesar_archivo(st.session_state["_ant_bytes"])
            if res_ant["errores"]:
                st.warning(":material/warning: El archivo del año anterior tiene errores, no se usará:")
                st.dataframe(pd.DataFrame(res_ant["errores"]), use_container_width=True, hide_index=True)
            else:
                mes_ant = mes_corte if mes_corte in res_ant["pivot_esf_crudo"].columns else res_ant["ultimo_mes"]
                eri_ant, esf_ant = calcular_estados(res_ant, mes_ant)
                st.success(f":material/check_circle: Archivo año anterior cargado: "
                           f"**{st.session_state.get('_ant_name','')}** (corte {mes_ant.title()})")

    c1, c2 = st.columns(2)
    with c1:
        md(f"**Vista previa ESF — saldo de cierre ({mes_corte.title()})**")
        filas_esf = [(NOMBRE_ESF.get(g, g).strip(), esf_act["grupos"].get(g, 0)) for g in GRUPOS_ESF_ORDEN]
        filas_esf += [("Capital emitido", esf_act["patrimonio"]["capital"]),
                      ("Superávit de capital", esf_act["patrimonio"]["superavit"]),
                      ("Reservas", esf_act["patrimonio"]["reservas"]),
                      ("Utilidad acumulada", esf_act["patrimonio"]["acumulada"]),
                      ("Utilidad del periodo", esf_act["patrimonio"]["periodo"])]
        st.dataframe(pd.DataFrame({"Cuenta": [f[0] for f in filas_esf],
                                   "Saldo": [fmt_cop(f[1]) for f in filas_esf]}),
                     use_container_width=True, hide_index=True, height=460)
        md(f"<p><b>Activos:</b> {fmt_cop(esf_act['total_activo'])} &nbsp;|&nbsp; "
           f"<b>Pasivos:</b> {fmt_cop(esf_act['total_pasivo'])} &nbsp;|&nbsp; "
           f"<b>Patrimonio:</b> {fmt_cop(esf_act['total_patrimonio'])}</p>"
           f"<p><b>Activos − Pasivos − Patrimonio:</b> {fmt_cop(esf_act['diferencia'])}</p>",
           unsafe_allow_html=True)
    with c2:
        md("**Vista previa ERI — acumulado hasta el corte**")
        claves = [("ing_ord", "Ingresos de actividades ordinarias"), ("otros_ing", "Otros ingresos"),
                  ("gtos_adm", "Gastos de administración"), ("otros_gto", "Otros gastos"),
                  ("ing_fin", "Ingresos financieros"), ("gto_fin", "Gastos financieros"),
                  ("util_ai", "Utilidad antes de impuesto"), ("impuesto", "Ingreso (gasto) por impuesto"),
                  ("util_per", "Utilidad del periodo")]
        st.dataframe(pd.DataFrame({"Línea": [c[1] for c in claves],
                                   "Valor": [fmt_cop(eri_act[c[0]]) for c in claves]}),
                     use_container_width=True, hide_index=True, height=370)

    md("---")
    if hay_dif:
        st.warning(":material/warning: Hay diferencias sin resolver (ver Validaciones). "
                   "El archivo se genera igual, mostrando los valores tal como se calculan.")
    with st.spinner("Preparando el archivo Excel…"):
        bytes_eeff = excel_eeff_en_bytes(
            empresa, nit, periodo, esf_act, eri_act, pivot_eri, df_eri_raw, df_esf_raw,
            esf_ant, eri_ant,
            (E.fecha_corte(mes_corte, anio), E.fecha_corte(mes_corte, anio - 1)),
            (anio, anio - 1))
    periodo_ant_msg = " (con período anterior)" if esf_ant else ""
    hojas = "ESF, ANEXO ESF, ERI, ANEXO ERI, ER MENSUALIZADO, CONSOL"
    st.success(f":material/check_circle: Archivo listo{periodo_ant_msg} — hojas: {hojas}")
    st.download_button(
        label=":material/download: Descargar EEFF_Formateado.xlsx",
        data=bytes_eeff,
        file_name="EEFF_Formateado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
