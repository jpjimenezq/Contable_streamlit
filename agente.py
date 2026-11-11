"""Agente de datos con Gemini: consulta un DataFrame en lenguaje natural.

Gemini no recibe el archivo completo. Recibe la estructura (columnas, tipos y unas pocas
filas de ejemplo) y la pregunta; para calcular, pide ejecutar código pandas, que corre
aquí, en el servidor de la aplicación, sobre los datos completos. El código no se muestra
a las personas que usan la aplicación; los cálculos quedan en `Conversacion.pasos` por si
hace falta revisarlos.

En el primer paso de cada pregunta se OBLIGA a Gemini a usar la herramienta de cálculo,
para que nunca responda cifras "de memoria".
"""
import ast
import builtins
import hashlib
import io
import os
import re
import time

import numpy as np
import pandas as pd
import streamlit as st

# ── Modelos ───────────────────────────────────────────────────────────────────
# Orden de preferencia para la capa gratuita. Los nombres y los cupos cambian con el
# tiempo: la lista se puede ajustar aquí, o escribir otro modelo en la pantalla.
MODELO_AUTOMATICO = "automatico"
MODELOS_INFO = [
    {"id": "gemini-3.5-flash-lite", "nombre": "Rápido y liviano",
     "cuando": "Para empezar y para preguntas directas: sumas, conteos, filtros, totales por grupo. "
               "Responde en pocos segundos y suele tener cupo disponible."},
    {"id": "gemini-3.1-flash-lite", "nombre": "Liviano (alternativa)",
     "cuando": "Úsalo si el anterior está lleno o no responde. Sirve para lo mismo."},
    {"id": "gemini-3.6-flash", "nombre": "Más preciso",
     "cuando": "Para preguntas largas o con varios pasos. Su cupo gratuito es muy pequeño "
               "(en las pruebas, 20 consultas al día; cada pregunta gasta 2 o más)."},
    {"id": "gemini-3.8-flash", "nombre": "El más nuevo",
     "cuando": "Es el más reciente, pero suele estar saturado. Úsalo solo si los demás fallan."},
]
MODELOS = [m["id"] for m in MODELOS_INFO]
MODELO_POR_DEFECTO = MODELO_AUTOMATICO

MAX_LLAMADAS_POR_PREGUNTA = 8
ESPERAS_REINTENTO = (2, 5)   # segundos antes de reintentar si Google está saturado (un solo modelo)
ESPERA_MAXIMA_429 = 40       # si Google pide esperar menos que esto, se espera y se reintenta
TIEMPO_LIMITE_MS = 45000     # tiempo máximo de espera por respuesta de Google
LIMITE_SALIDA = 6000         # caracteres que se devuelven al modelo por cada cálculo

INSTRUCCION = """Eres un analista de datos que ayuda a personas del área contable.
Trabajas sobre un DataFrame de pandas llamado `df` que ya está cargado.

Reglas:
- Para obtener cualquier cifra, filtro, suma o conteo usa SIEMPRE la herramienta `ejecutar_codigo_pandas`.
  Nunca inventes ni estimes valores, ni uses solo las filas de ejemplo: calcula con la herramienta
  sobre todo el DataFrame.
- Dentro de la herramienta están disponibles `df`, `pd` y `np`. No se permiten imports,
  leer ni escribir archivos. Cada ejecución parte del `df` original.
- Si el código falla, corrígelo y vuelve a intentarlo.
- Responde siempre en español, de forma clara y breve, para una persona del área contable que
  no sabe de programación ni de sistemas.
- NUNCA muestres código, ni nombres de variables, ni términos técnicos (DataFrame, df, pandas,
  Python, columnas «Unnamed»). No uses formato de código ni comillas invertidas. Menciona las
  columnas por su nombre normal, entre comillas comunes, por ejemplo: la columna "VALOR".
- Escribe los montos con separador de miles y menciona de qué columna salieron.
- Si hay filas que parecen saldos o totales mezcladas con movimientos (por ejemplo "SALDO INICIAL"
  o "SALDO DIA"), no las sumes como si fueran movimientos: calcula sin ellas y avísalo.
- Si la pregunta no se puede responder con estos datos, dilo.
"""


class ErrorAgente(Exception):
    """Error con un mensaje listo para mostrar al usuario."""


# ── Ejecución controlada del código que propone el modelo ─────────────────────
# Es una protección razonable, no un aislamiento total: sirve para evitar errores y
# usos indebidos evidentes, pero conviene usar el agente con datos de prueba.
_BUILTINS_PERMITIDOS = {
    "len", "sum", "min", "max", "abs", "round", "sorted", "range", "enumerate", "zip", "map",
    "filter", "list", "dict", "set", "tuple", "str", "int", "float", "bool", "isinstance",
    "any", "all", "reversed", "divmod", "pow", "True", "False", "None",
}
_NOMBRES_BLOQUEADOS = {
    "open", "exec", "eval", "compile", "input", "globals", "locals", "vars", "getattr",
    "setattr", "delattr", "breakpoint", "exit", "quit", "help", "dir", "memoryview",
    "os", "sys", "subprocess", "importlib", "builtins",
}
_ATRIBUTOS_BLOQUEADOS = {
    "to_csv", "to_excel", "to_pickle", "to_parquet", "to_sql", "to_feather", "to_hdf",
    "to_stata", "to_clipboard", "to_json", "to_html", "to_latex", "to_xml", "to_orc",
    "eval", "load", "save", "savez", "savetxt", "fromfile", "tofile", "loadtxt", "genfromtxt",
}


class CodigoNoPermitido(Exception):
    pass


def validar_codigo(codigo: str) -> ast.Module:
    arbol = ast.parse(codigo)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            raise CodigoNoPermitido("no se permiten imports; `df`, `pd` y `np` ya están disponibles")
        if isinstance(nodo, (ast.While, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await)):
            raise CodigoNoPermitido("esa instrucción no está permitida")
        if isinstance(nodo, ast.Attribute):
            if nodo.attr.startswith("_") or nodo.attr.startswith("read_") or nodo.attr in _ATRIBUTOS_BLOQUEADOS:
                raise CodigoNoPermitido(f"el atributo `{nodo.attr}` no está permitido")
        if isinstance(nodo, ast.Name) and (nodo.id in _NOMBRES_BLOQUEADOS or nodo.id.startswith("__")):
            raise CodigoNoPermitido(f"el nombre `{nodo.id}` no está permitido")
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and "__" in nodo.value:
            raise CodigoNoPermitido("no se permiten textos con `__`")
    return arbol


def _formatear(valor) -> str:
    try:
        if isinstance(valor, pd.DataFrame):
            return valor.to_string(max_rows=60, max_cols=20)
        if isinstance(valor, pd.Series):
            return valor.to_string(max_rows=60)
        return repr(valor)
    except Exception as e:
        return f"(no se pudo mostrar el resultado: {type(e).__name__}: {e})"


def ejecutar_codigo(df: pd.DataFrame, codigo: str, limite: int = LIMITE_SALIDA) -> str:
    """Ejecuta `codigo` sobre una copia de `df` y devuelve lo impreso y el valor final."""
    try:
        arbol = validar_codigo(codigo)
    except SyntaxError as e:
        return f"Error de sintaxis: {e}"
    except CodigoNoPermitido as e:
        return f"Código no permitido: {e}"

    salida = io.StringIO()

    def _print(*args, **kwargs):
        kwargs.pop("file", None)
        print(*args, file=salida, **kwargs)

    permitidos = {n: getattr(builtins, n) for n in _BUILTINS_PERMITIDOS if hasattr(builtins, n)}
    permitidos["print"] = _print
    entorno = {"__builtins__": permitidos, "df": df.copy(), "pd": pd, "np": np}

    try:
        cuerpo = list(arbol.body)
        ultima = ast.Expression(cuerpo.pop().value) if cuerpo and isinstance(cuerpo[-1], ast.Expr) else None
        modulo = ast.fix_missing_locations(ast.Module(body=cuerpo, type_ignores=[]))
        exec(compile(modulo, "<agente>", "exec"), entorno)
        valor = None
        if ultima is not None:
            valor = eval(compile(ast.fix_missing_locations(ultima), "<agente>", "eval"), entorno)
    except Exception as e:  # el error vuelve al modelo para que corrija el código
        return f"Error al ejecutar: {type(e).__name__}: {e}"

    texto = salida.getvalue()
    if valor is not None:
        texto += _formatear(valor)
    texto = texto.strip() or "(el código se ejecutó sin imprimir nada)"
    if len(texto) > limite:
        texto = texto[:limite] + "\n... (salida recortada)"
    return texto


# ── Descripción de los datos que se envía al modelo ───────────────────────────
def descripcion_df(df: pd.DataFrame, filas_ejemplo: int = 3, max_columnas: int = 60) -> str:
    columnas = list(df.columns)[:max_columnas]
    lineas = [f"El DataFrame `df` tiene {len(df)} filas y {len(df.columns)} columnas.", "Columnas (tipo, nulos):"]
    for c in columnas:
        lineas.append(f"- {c!r}: {df[c].dtype}, {int(df[c].isna().sum())} nulos")
    if len(df.columns) > max_columnas:
        lineas.append(f"... y {len(df.columns) - max_columnas} columnas más.")
    if filas_ejemplo:
        lineas += [f"Primeras {filas_ejemplo} filas:", df[columnas].head(filas_ejemplo).to_string(max_colwidth=40)]
    return "\n".join(lineas)


# ── Clave y cliente de Gemini ─────────────────────────────────────────────────
def obtener_clave():
    """Devuelve (clave, origen). Busca en los secretos y en la variable GEMINI_API_KEY."""
    try:
        clave = st.secrets.get("gemini", {}).get("api_key", "")
    except Exception:
        clave = ""
    if clave and not clave.startswith("PEGA_"):
        return clave.strip(), "los secretos de la aplicación"
    clave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if clave:
        return clave.strip(), "la variable de entorno GEMINI_API_KEY"
    return "", ""


def modelo_configurado() -> str:
    """Modelo fijado en los secretos (`model`) o el modo automático."""
    try:
        return st.secrets.get("gemini", {}).get("model", "") or MODELO_POR_DEFECTO
    except Exception:
        return MODELO_POR_DEFECTO


def etiqueta_modelo(modelo: str) -> str:
    if modelo == MODELO_AUTOMATICO:
        return "Automático (recomendado): prueba uno y pasa al siguiente si falla"
    for m in MODELOS_INFO:
        if m["id"] == modelo:
            return f"{m['nombre']} · {modelo}"
    return modelo


def firma_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()[:12]


def crear_cliente(clave: str):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=clave, http_options=types.HttpOptions(timeout=TIEMPO_LIMITE_MS))


# ── Errores de Gemini ─────────────────────────────────────────────────────────
def codigo_error(exc: Exception):
    codigo = getattr(exc, "code", None)
    if isinstance(codigo, int):
        return codigo
    if "timeout" in type(exc).__name__.lower():
        return 504
    return None


def _texto_error(exc: Exception) -> str:
    return str(getattr(exc, "message", "") or exc)


def es_cupo_diario(exc: Exception) -> bool:
    bajo = _texto_error(exc).lower()
    return codigo_error(exc) == 429 and ("per day" in bajo or "perday" in bajo or "daily" in bajo)


def espera_sugerida(exc: Exception):
    """Segundos que Google pide esperar tras un 429, si son pocos; si no, None."""
    if codigo_error(exc) != 429 or es_cupo_diario(exc):
        return None
    m = re.search(r"retry in ([\d.]+)s", _texto_error(exc))
    if m:
        segundos = float(m.group(1))
        return segundos if segundos <= ESPERA_MAXIMA_429 else None
    return None


def es_error_de_modelo(exc: Exception) -> bool:
    """Fallos que dependen del modelo (cupo, saturación, no disponible): conviene probar otro."""
    return codigo_error(exc) in (404, 429, 500, 502, 503, 504)


def es_error_transitorio(exc: Exception) -> bool:
    """Errores del servicio de Google (5xx) que suelen resolverse reintentando."""
    return codigo_error(exc) in (500, 502, 503, 504)


def traducir_error(exc: Exception) -> str:
    """Convierte un error del SDK en un mensaje claro para el usuario."""
    codigo = codigo_error(exc)
    texto = _texto_error(exc)
    bajo = texto.lower()
    if codigo in (400, 401, 403) and ("api key" in bajo or "api_key" in bajo or codigo in (401, 403)):
        return ("La clave de Gemini no es válida o no tiene permiso. Revisa que la copiaste completa "
                "desde Google AI Studio.")
    if codigo == 404:
        return ("El modelo elegido no existe o ya no está disponible para tu cuenta. Elige «Automático» "
                "u otro modelo de la lista.")
    if codigo == 429:
        if es_cupo_diario(exc):
            return ("Se agotó el cupo diario gratuito de este modelo (se renueva al día siguiente). "
                    "Elige «Automático» u otro modelo de la lista.")
        return ("Se alcanzó el límite por minuto de la capa gratuita. Espera un minuto y vuelve a intentar.")
    if codigo and codigo >= 500:
        return (f"El servicio de Gemini está saturado o no responde (error {codigo}). "
                "Espera un momento o elige otro modelo de la lista.")
    if codigo:
        return f"Gemini devolvió un error ({codigo}): {texto[:300]}"
    return f"No se pudo consultar a Gemini: {texto[:300]}"


def explicar_sin_texto(respuesta) -> str:
    """Dice por qué Gemini no devolvió texto, para que la persona sepa qué cambiar."""
    comentario = getattr(respuesta, "prompt_feedback", None)
    if comentario is not None and getattr(comentario, "block_reason", None):
        return ("Gemini no aceptó la pregunta por sus filtros de seguridad. "
                "Reformúlala con otras palabras.")
    candidatos = getattr(respuesta, "candidates", None) or []
    if candidatos:
        motivo = str(getattr(candidatos[0], "finish_reason", "") or "")
        if "MAX_TOKENS" in motivo:
            return ("La respuesta salió demasiado larga y se cortó. Pide algo más corto, "
                    "por ejemplo «los 10 primeros».")
        if any(palabra in motivo for palabra in ("SAFETY", "BLOCK", "PROHIBITED", "RECITATION")):
            return ("Gemini bloqueó la respuesta por sus filtros de seguridad. "
                    "Reformula la pregunta con otras palabras.")
    return ("Gemini no devolvió una respuesta. Prueba a reformular la pregunta con los nombres "
            "de las columnas, o elige otro modelo.")


class _FalloDeModelo(Exception):
    """Un modelo no pudo responder (cupo, saturación...): se puede intentar con otro."""

    def __init__(self, original: Exception):
        super().__init__(str(original))
        self.original = original


# ── Conversación ──────────────────────────────────────────────────────────────
class Conversacion:
    """Chat con memoria sobre un DataFrame. Con `modelo=MODELO_AUTOMATICO` pasa al siguiente
    modelo de la lista cuando uno no está disponible, conservando el historial."""

    def __init__(self, cliente, df: pd.DataFrame, modelo: str = MODELO_AUTOMATICO):
        from google.genai import types
        self._types = types
        self.cliente = cliente  # se guarda: si nadie lo referencia, el SDK cierra la conexión
        self.df = df
        self.automatico = modelo == MODELO_AUTOMATICO
        self.candidatos = MODELOS[:] if self.automatico else [modelo]
        self.indice = 0
        self.pasos = []
        self.fallos = []  # (modelo, código) de los intentos fallidos de la pregunta en curso

        def ejecutar_codigo_pandas(codigo: str) -> str:
            """Ejecuta código Python con pandas sobre el DataFrame `df` y devuelve lo que imprime o el
            valor de la última expresión. Están disponibles `df`, `pd` y `np`; no se permiten imports.

            Args:
                codigo: Código Python a ejecutar. Ejemplo: df['Valor'].sum()
            """
            return self._ejecutar(codigo)

        self._config = types.GenerateContentConfig(
            system_instruction=INSTRUCCION + "\n" + descripcion_df(df),
            tools=[ejecutar_codigo_pandas],
            temperature=0.2,
            # Los cálculos se ejecutan en `_vuelta`, no dentro del SDK, para poder forzar el primero.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        self.chat = self._nuevo_chat(self.modelo_actual, None)

    @property
    def modelo_actual(self) -> str:
        return self.candidatos[self.indice]

    def _nuevo_chat(self, modelo: str, historial):
        return self.cliente.chats.create(model=modelo, config=self._config, history=historial)

    def _ejecutar(self, codigo: str) -> str:
        salida = ejecutar_codigo(self.df, codigo)
        self.pasos.append({"codigo": codigo, "salida": salida})
        return salida

    def _config_turno(self, forzar_herramienta: bool):
        t = self._types
        modo = "ANY" if forzar_herramienta else "AUTO"
        return self._config.model_copy(update={
            "tool_config": t.ToolConfig(function_calling_config=t.FunctionCallingConfig(mode=modo)),
        })

    def _enviar(self, mensaje, forzar_herramienta: bool):
        """Un envío a Gemini con reintentos. Lanza _FalloDeModelo o ErrorAgente."""
        hay_otro = self.automatico and self.indice + 1 < len(self.candidatos)
        esperas = () if hay_otro else ESPERAS_REINTENTO  # con alternativa, se cambia de modelo ya
        intento = 0
        espero_429 = False
        while True:
            try:
                return self.chat.send_message(mensaje, config=self._config_turno(forzar_herramienta))
            except Exception as e:
                if not es_error_de_modelo(e):
                    raise ErrorAgente(traducir_error(e)) from e
                pausa = espera_sugerida(e)
                if pausa is not None and not espero_429 and not hay_otro:
                    espero_429 = True
                    time.sleep(pausa + 1)
                    continue
                if es_error_transitorio(e) and intento < len(esperas):
                    time.sleep(esperas[intento])
                    intento += 1
                    continue
                raise _FalloDeModelo(e) from e

    def _vuelta(self, pregunta: str) -> str:
        t = self._types
        mensaje = pregunta
        for n in range(MAX_LLAMADAS_POR_PREGUNTA + 1):
            respuesta = self._enviar(mensaje, forzar_herramienta=(n == 0))
            llamadas = list(getattr(respuesta, "function_calls", None) or [])
            if not llamadas:
                texto = (getattr(respuesta, "text", None) or "").strip()
                if not texto:
                    raise ErrorAgente(explicar_sin_texto(respuesta))
                return texto
            if n == MAX_LLAMADAS_POR_PREGUNTA:
                raise ErrorAgente("Para esta pregunta Gemini necesitaba más cálculos de los permitidos. "
                                  "Divídela en preguntas más pequeñas.")
            partes = []
            for fc in llamadas:
                codigo = (fc.args or {}).get("codigo", "")
                partes.append(t.Part.from_function_response(
                    name=fc.name, response={"resultado": self._ejecutar(codigo)}))
            mensaje = partes
        raise ErrorAgente("No se pudo completar la consulta.")  # pragma: no cover

    def preguntar(self, pregunta: str):
        """Devuelve (respuesta, pasos, modelo_usado). Lanza ErrorAgente con un mensaje claro."""
        historial = self.chat.get_history()  # para volver atrás si la pregunta falla a medias
        self.fallos = []
        while True:
            self.pasos = []
            try:
                texto = self._vuelta(pregunta)
                return texto, list(self.pasos), self.modelo_actual
            except _FalloDeModelo as f:
                self.fallos.append((self.modelo_actual, codigo_error(f.original), es_cupo_diario(f.original)))
                if self.automatico and self.indice + 1 < len(self.candidatos):
                    self.indice += 1
                    self.chat = self._nuevo_chat(self.modelo_actual, historial)
                    continue
                self.chat = self._nuevo_chat(self.modelo_actual, historial)
                raise ErrorAgente(self._mensaje_final(f.original)) from f.original
            except ErrorAgente:
                self.chat = self._nuevo_chat(self.modelo_actual, historial)
                raise

    def _mensaje_final(self, ultimo: Exception) -> str:
        if self.automatico and len(self.fallos) > 1:
            diario = sum(1 for _, _, d in self.fallos if d)
            if diario == len(self.fallos):
                return ("Se agotó hoy el cupo gratuito de todos los modelos. Intenta de nuevo mañana "
                        "o usa otra clave.")
            return ("Ahora mismo ningún modelo gratuito pudo responder (cupo agotado o servicio saturado). "
                    "Espera unos minutos y vuelve a intentar.")
        return traducir_error(ultimo)
