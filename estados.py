"""Cálculos y validaciones de los estados financieros (ESF y ERI) desde la hoja terceros_.

Convenciones del archivo de Anexos (comprobadas con el caso de diciembre de 2025):
- En `Saldo Mes`, los activos y los gastos vienen positivos, y los pasivos, el patrimonio y los
  ingresos vienen negativos (naturaleza contable).
- ESF: `Saldo Mes` es el saldo de cierre de cada mes. Se usa solo el mes de corte.
- ERI: `Saldo Mes` es el movimiento de cada mes. Se suman los meses hasta el corte.
- Todas las líneas se presentan con signo (sin valor absoluto): activos = +saldo, pasivos y
  patrimonio = −saldo, y cada línea del ERI = −saldo (ingresos positivos, gastos negativos).
"""
import calendar
import datetime
from collections import defaultdict

import pandas as pd

MESES_ORDEN = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
               "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

GRUPOS_ERI = ["INGRESOS DE ACTIVIDADES ORDINARIAS", "OTROS INGRESOS",
              "GASTOS DE ADMINISTRACION", "OTROS GASTOS",
              "INGRESOS FINANCIEROS", "GASTOS FINANCIEROS", "PROVISION DE IMPUESTOS"]
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

COLUMNAS_REQUERIDAS = ["Codigo", "Nombre cuenta", "Nit", "Nombre tercero",
                       "Mes", "Saldo Mes", "Cuenta", "Grupo"]

# Cuentas del patrimonio (PUC) que alimentan cada línea del ESF
CUENTAS_PATRIMONIO = {
    "capital":   ("31",),          # Capital emitido
    "superavit": ("32",),          # Superávit de capital
    "reservas":  ("33",),          # Reservas
    "acumulada": ("36", "37"),     # Utilidad o pérdida acumulada
}
CLASES_RESULTADO = ("4", "5", "6", "7")  # ingresos, gastos, costos de ventas y de producción

_MESES_ANTERIOR = {"PERIODO ANTERIOR", "PERÍODO ANTERIOR", "PERIOD ANTERIOR",
                   "ANO ANTERIOR", "AÑO ANTERIOR", "ANTERIOR",
                   "PERIODOANT", "PERIODOANTER", "PER ANTERIOR"}


def es_mes_anterior(nombre_mes) -> bool:
    """True si el valor de la columna Mes indica "período anterior"."""
    s = str(nombre_mes).strip().upper()
    if s in _MESES_ANTERIOR:
        return True
    return "ANTERIOR" in s or ("PERIOD" in s and "ANT" in s)


# ── Fechas y encabezados ──────────────────────────────────────────────────────
def numero_mes(mes: str) -> int:
    return MESES_ORDEN.index(mes) + 1


def fecha_corte(mes: str, anio: int) -> datetime.date:
    """Último día del mes de corte."""
    n = numero_mes(mes)
    return datetime.date(anio, n, calendar.monthrange(anio, n)[1])


def texto_periodo(mes: str, anio: int) -> str:
    """Ejemplo: AL 31 DE DICIEMBRE DE 2025 Y 31 DE DICIEMBRE DE 2024."""
    actual, anterior = fecha_corte(mes, anio), fecha_corte(mes, anio - 1)
    return f"AL {actual.day} DE {mes} DE {anio} Y {anterior.day} DE {mes} DE {anio - 1}"


# ── Preparación de datos ──────────────────────────────────────────────────────
def codigo_texto(serie: pd.Series) -> pd.Series:
    """Código de cuenta como texto de dígitos ("" si no es numérico)."""
    num = pd.to_numeric(serie, errors="coerce")
    return num.round().astype("Int64").astype(str).where(num.notna(), "")


def _clave_grupo(nombre) -> str:
    return str(nombre).strip().upper()


def normalizar_grupos(serie: pd.Series) -> pd.Series:
    """Unifica mayúsculas y espacios de los grupos con los nombres oficiales de la lista."""
    canon = {_clave_grupo(g): g for g in GRUPOS_ERI + GRUPOS_ESF_ACTIVO + GRUPOS_ESF_PASIVO}
    return serie.map(lambda x: canon.get(_clave_grupo(x), x) if pd.notna(x) else x)


def meses_hasta(mes: str):
    return MESES_ORDEN[: numero_mes(mes)]


# ── Validación del archivo al cargarlo ────────────────────────────────────────
def validar_entrada(df: pd.DataFrame):
    """Revisa la hoja terceros_ tal como se leyó. Devuelve (errores, avisos).

    Cada incidencia es un dict: fila (de Excel, o None), columna y motivo.
    Los errores impiden calcular; los avisos no.
    """
    errores, avisos = [], []
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        errores.append({"fila": None, "columna": ", ".join(faltan),
                        "motivo": "Faltan columnas en la hoja terceros_"})
        return errores, avisos

    # Importes: la primera fila de datos es la 2 de Excel (la 1 trae los encabezados)
    bruto = df["Saldo Mes"]
    numero = pd.to_numeric(bruto, errors="coerce")
    mal = df[bruto.notna() & numero.isna() & (bruto.astype(str).str.strip() != "")]
    for idx, fila in mal.head(20).iterrows():
        errores.append({"fila": int(idx) + 2, "columna": "Saldo Mes",
                        "motivo": f"El importe «{fila['Saldo Mes']}» no es un número"})
    if len(mal) > 20:
        errores.append({"fila": None, "columna": "Saldo Mes",
                        "motivo": f"Hay {len(mal) - 20} importes inválidos más"})

    # Meses
    mes = df["Mes"].astype(str).str.strip().str.upper()
    sin_mes = df[df["Mes"].isna() & (numero.fillna(0) != 0)]
    for idx in sin_mes.index[:10]:
        errores.append({"fila": int(idx) + 2, "columna": "Mes",
                        "motivo": "La fila tiene importe pero no tiene mes"})
    raros = df[df["Mes"].notna() & ~mes.isin(MESES_ORDEN) & ~df["Mes"].map(es_mes_anterior)]
    for valor, g in raros.groupby(raros["Mes"].astype(str)):
        errores.append({"fila": int(g.index[0]) + 2, "columna": "Mes",
                        "motivo": f"El mes «{valor}» no se reconoce ({len(g)} filas)"})

    # Grupos que el programa no conoce: no entrarían en ningún estado
    conocidos = {_clave_grupo(g) for g in GRUPOS_ERI + GRUPOS_ESF_ACTIVO + GRUPOS_ESF_PASIVO}
    grupo = df["Grupo"].dropna().astype(str)
    grupo = grupo[~grupo.map(_clave_grupo).isin(conocidos) & (grupo.str.strip() != "")]
    for nombre, g in grupo.groupby(grupo):
        importe = float(numero.loc[g.index].fillna(0).sum())
        avisos.append({"fila": int(g.index[0]) + 2, "columna": "Grupo",
                       "motivo": (f"El grupo «{nombre}» no está en la lista del programa: sus {len(g)} filas "
                                  f"({importe:,.2f}) no entran en ningún estado")})
    return errores, avisos


# ── Saldos de cuentas del Anexo ───────────────────────────────────────────────
def _prefijos(codigos) -> set:
    """Códigos que tienen otras cuentas por debajo (son totales de jerarquía)."""
    out = set()
    for c in set(codigos):
        for i in range(1, len(c)):
            out.add(c[:i])
    return out


def saldo_cuenta(base: pd.DataFrame, codigo: str, meses=None):
    """Saldo de una cuenta en el Anexo para los meses dados (None = todos).

    Usa la fila de total de la cuenta (la que no trae tercero). Si el archivo no la trae,
    suma las cuentas de detalle. Devuelve None si el código no aparece.
    """
    d = base if meses is None else base[base["Mes"].isin(list(meses))]
    padre = d[(d["cod"] == codigo) & d["Nit"].isna()]
    if len(padre):
        return float(padre["Saldo Mes"].sum())
    debajo = d[d["cod"].str.startswith(codigo) & (d["cod"] != "")]
    if debajo.empty:
        return None
    hojas = debajo[~debajo["cod"].isin(_prefijos(base["cod"]))]
    return float(hojas["Saldo Mes"].sum())


def saldos_patrimonio(base: pd.DataFrame, mes=None) -> dict:
    """Capital, superávit, reservas y utilidad acumulada (valores positivos si son créditos)."""
    meses = None if mes is None else [mes]
    out = {}
    for linea, cuentas in CUENTAS_PATRIMONIO.items():
        partes = [saldo_cuenta(base, c, meses) for c in cuentas]
        out[linea] = -sum(p for p in partes if p is not None)
    return out


# ── Líneas de los estados (con signo de presentación) ─────────────────────────
def totales_hasta(pivot_eri: pd.DataFrame, mes: str) -> dict:
    """ERI acumulado por grupo: suma de los meses hasta el corte."""
    cols = [m for m in meses_hasta(mes) if m in pivot_eri.columns]
    return {g: (float(pivot_eri.loc[g, cols].sum()) if g in pivot_eri.index else 0.0) for g in GRUPOS_ERI}


def saldos_en_mes(pivot_esf: pd.DataFrame, mes: str) -> dict:
    """ESF: saldo de cierre por grupo en el mes de corte."""
    grupos = GRUPOS_ESF_ACTIVO + GRUPOS_ESF_PASIVO
    return {g: (float(pivot_esf.loc[g, mes]) if g in pivot_esf.index and mes in pivot_esf.columns else 0.0)
            for g in grupos}


def lineas_eri(totales: dict) -> dict:
    """Cada línea = −(suma de Saldo Mes): ingresos positivos y gastos negativos."""
    v = lambda g: -float(totales.get(g, 0) or 0)
    ing_ord, otros_ing, ing_fin = v("INGRESOS DE ACTIVIDADES ORDINARIAS"), v("OTROS INGRESOS"), v("INGRESOS FINANCIEROS")
    gtos_adm, otros_gto, gto_fin = v("GASTOS DE ADMINISTRACION"), v("OTROS GASTOS"), v("GASTOS FINANCIEROS")
    impuesto = v("PROVISION DE IMPUESTOS")
    util_ai = ing_ord + otros_ing + gtos_adm + otros_gto + ing_fin + gto_fin
    return {
        "ing_ord": ing_ord, "otros_ing": otros_ing, "gtos_adm": gtos_adm, "otros_gto": otros_gto,
        "ing_fin": ing_fin, "gto_fin": gto_fin, "impuesto": impuesto,
        "ganancia_bruta": ing_ord, "util_ai": util_ai, "util_per": util_ai + impuesto,
        "ingresos": ing_ord + otros_ing + ing_fin,
        "gastos": gtos_adm + otros_gto + gto_fin + impuesto,
    }


def lineas_esf(saldos: dict, patrimonio: dict, utilidad: float) -> dict:
    """Activos = +saldo; pasivos = −saldo; patrimonio = cuentas 31 a 37 más la utilidad del período."""
    grupos = {g: float(saldos.get(g, 0) or 0) for g in GRUPOS_ESF_ACTIVO}
    grupos.update({g: -float(saldos.get(g, 0) or 0) for g in GRUPOS_ESF_PASIVO})
    total_activo = sum(grupos[g] for g in GRUPOS_ESF_ACTIVO)
    total_pasivo = sum(grupos[g] for g in GRUPOS_ESF_PASIVO)
    pat = {k: float(patrimonio.get(k, 0) or 0) for k in CUENTAS_PATRIMONIO}
    pat["periodo"] = float(utilidad)
    total_pat = sum(pat.values())
    return {"grupos": grupos, "patrimonio": pat, "total_activo": total_activo,
            "total_pasivo": total_pasivo, "total_patrimonio": total_pat,
            "diferencia": total_activo - total_pasivo - total_pat}


# ── Validaciones de totales contra el Anexo ───────────────────────────────────
def validar_totales(base: pd.DataFrame, mes: str, esf: dict, eri: dict, tolerancia: float) -> list:
    """Compara lo calculado con los totales que trae el propio Anexo."""
    def fila(nombre, calculado, anexo, nota):
        if anexo is None:
            return {"control": nombre, "calculado": calculado, "anexo": None, "diferencia": None,
                    "estado": "Sin dato", "nota": "El Anexo no trae la fila de total de esta cuenta."}
        dif = calculado - anexo
        return {"control": nombre, "calculado": calculado, "anexo": anexo, "diferencia": dif,
                "estado": "Cuadra" if abs(dif) <= tolerancia else "Diferencia", "nota": nota}

    al_corte = [mes]
    activo = saldo_cuenta(base, "1", al_corte)
    pasivo = saldo_cuenta(base, "2", al_corte)
    patrim = saldo_cuenta(base, "3", al_corte)
    clases = [saldo_cuenta(base, c, meses_hasta(mes)) for c in CLASES_RESULTADO]
    resultado = None if all(c is None for c in clases) else -sum(c for c in clases if c is not None)
    pat = esf["patrimonio"]
    patrimonio_cuentas = sum(v for k, v in pat.items() if k != "periodo")

    return [
        fila(f"Total activos ({mes.title()})", esf["total_activo"], activo,
             "Suma de las líneas de activo contra la cuenta 1 del Anexo."),
        fila(f"Total pasivos ({mes.title()})", esf["total_pasivo"], None if pasivo is None else -pasivo,
             "Suma de las líneas de pasivo contra la cuenta 2 del Anexo."),
        fila(f"Patrimonio, cuentas 31 a 37 ({mes.title()})", patrimonio_cuentas, None if patrim is None else -patrim,
             "Si hay diferencia, hay cuentas de patrimonio (por ejemplo la 34, 35 o 38) que no están en ninguna línea."),
        fila("Ecuación: Activo − Pasivo − Patrimonio", esf["diferencia"], 0.0,
             "Debe ser cero. El patrimonio incluye la utilidad del período del ERI."),
        fila("Resultado del período (ERI)", eri["util_per"], resultado,
             "Resultado por grupos contra el total de las cuentas 4 a 7 del Anexo. "
             "Si no cuadra, mira los totales que no coinciden con su detalle."),
    ]


def descuadres_jerarquia(base: pd.DataFrame, tolerancia: float, mes_corte: str) -> pd.DataFrame:
    """Cuentas cuyo total en el Anexo no es igual a la suma de su detalle (por mes)."""
    columnas = ["Mes", "Código", "Cuenta", "Total en el Anexo", "Suma del detalle", "Diferencia", "Afecta"]
    d = base[base["cod"] != ""]
    prefijos = _prefijos(d["cod"])
    hojas = d[~d["cod"].isin(prefijos)]
    sumas = defaultdict(float)
    for mes, cod, valor in zip(hojas["Mes"], hojas["cod"], hojas["Saldo Mes"]):
        for i in range(1, len(cod) + 1):
            sumas[(mes, cod[:i])] += float(valor)
    padres = (d[d["cod"].isin(prefijos) & d["Nit"].isna()]
              .groupby(["Mes", "cod"], as_index=False)
              .agg({"Nombre cuenta": "first", "Saldo Mes": "sum"}))
    filas = []
    for _, r in padres.iterrows():
        detalle = sumas.get((r["Mes"], r["cod"]), 0.0)
        dif = float(r["Saldo Mes"]) - detalle
        if abs(dif) <= tolerancia:
            continue
        if r["cod"][0] in CLASES_RESULTADO:
            afecta = "ERI"
        elif r["Mes"] == mes_corte:
            afecta = "ESF del corte"
        else:
            afecta = "Otro mes"
        filas.append((r["Mes"], r["cod"], r["Nombre cuenta"], float(r["Saldo Mes"]), detalle, dif, afecta))
    out = pd.DataFrame(filas, columns=columnas)
    if out.empty:
        return out
    orden = {m: i for i, m in enumerate(MESES_ORDEN)}
    out["_m"] = out["Mes"].map(orden)
    out["_a"] = out["Diferencia"].abs()
    out = out.sort_values(["_a"], ascending=False).drop(columns=["_m", "_a"]).reset_index(drop=True)
    return out
