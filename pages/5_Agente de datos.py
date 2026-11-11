import streamlit as st
from ui import inject_css, md, page_header, empty_state

# Los estilos van primero: así la página se ve con el diseño del portal desde el
# primer instante, antes de cargar las librerías pesadas.
st.set_page_config(
    page_title="Agente de Datos",
    page_icon=":material/smart_toy:",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_css()

from sesion import requerir_sesion
requerir_sesion()

import pandas as pd
import agente

AVATAR_USUARIO = ":material/person:"
AVATAR_AGENTE = ":material/smart_toy:"
SUGERENCIAS = [
    "Dame un resumen del archivo",
    "¿Cuánto suman los valores de cada columna numérica?",
    "¿Hay filas con datos vacíos?",
]

page_header(
    'Agente de Datos',
    'Carga un archivo CSV o Excel y conversa con él: pregunta, y sigue preguntando sobre las respuestas. '
    'Funciona con Gemini (capa gratuita).',
    'bot',
)

# ── Archivo ──────────────────────────────────────────────────────────────────
md('<p class="section-title">[[file-text]] Archivo de datos (CSV o Excel)</p>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Sube tu archivo para explorar:",
    type=['csv', 'xlsx', 'xls'],
    label_visibility="collapsed"
)

if uploaded_file is None:
    empty_state('Carga un archivo de datos para conversar con él', 'Formatos soportados: CSV, Excel (.xlsx, .xls)')
    st.stop()

try:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f":material/cancel: Error al cargar el archivo. ¿Verificaste el formato? ({str(e)})")
    st.stop()

st.success(f":material/check_circle: Archivo cargado exitosamente: {uploaded_file.name}")

col1, col2, col3 = st.columns(3)
with col1:
    md(f"""
    <div class="metric-card">
        <div class="number">{df.shape[0]}</div>
        <div class="label">Filas</div>
    </div>""", unsafe_allow_html=True)
with col2:
    md(f"""
    <div class="metric-card">
        <div class="number">{df.shape[1]}</div>
        <div class="label">Columnas</div>
    </div>""", unsafe_allow_html=True)
with col3:
    tamano_kb = df.memory_usage(deep=True).sum() / 1024
    md(f"""
    <div class="metric-card">
        <div class="number">{tamano_kb:.1f}</div>
        <div class="label">Tamaño (KB)</div>
    </div>""", unsafe_allow_html=True)

with st.expander(":material/visibility: Ver los datos del archivo"):
    tab1, tab2, tab3 = st.tabs([":material/assignment: Datos", ":material/trending_up: Información", ":material/search: Estadísticas"])

    with tab1:
        st.dataframe(df.head(100), use_container_width=True)

    with tab2:
        st.write("**Estructura del Dataset:**")
        info_df = pd.DataFrame({
            'Columna': df.columns,
            'Tipo': df.dtypes.astype(str),
            'No Nulos': df.count(),
            'Nulos': df.isnull().sum(),
            '% Nulos': (df.isnull().sum() / len(df) * 100).round(2)
        })
        st.dataframe(info_df, use_container_width=True)

    with tab3:
        st.write("**Estadísticas Descriptivas:**")
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            st.dataframe(numeric_df.describe(), use_container_width=True)
        else:
            st.info("No hay columnas numéricas para mostrar estadísticas.")


# ── Asistente de IA (Gemini) ─────────────────────────────────────────────────
md('<p class="section-title">[[bot]] Conversa con tus datos</p>', unsafe_allow_html=True)

st.info(
    ":material/info: Con la capa gratuita de Gemini, Google puede usar lo que se envía para mejorar sus "
    "productos. Se envían las columnas, unas filas de ejemplo y las preguntas. "
    "**Usa solo datos de prueba, sin información confidencial.**"
)

clave, origen = agente.obtener_clave()
modelo_actual = agente.modelo_configurado()
OTRO = "Otro modelo…"
opciones = [agente.MODELO_AUTOMATICO] + agente.MODELOS + [OTRO]
if modelo_actual not in opciones:
    opciones.insert(1, modelo_actual)

with st.expander(":material/tune: Configuración de Gemini", expanded=not clave):
    modelo = st.selectbox(
        "Modelo",
        opciones,
        index=opciones.index(modelo_actual),
        format_func=agente.etiqueta_modelo,
        key="agente_modelo",
    )
    if modelo == OTRO:
        modelo = st.text_input("Nombre del modelo", value="", key="agente_modelo_otro").strip()
    st.markdown("**¿Cuál elijo?**")
    st.markdown(
        "- **Automático (recomendado):** empieza por el más liviano y, si está lleno o saturado, "
        "pasa solo al siguiente. No tienes que hacer nada.\n"
        + "".join(f"- **{m['nombre']}** (`{m['id']}`): {m['cuando']}\n" for m in agente.MODELOS_INFO)
    )
    st.caption("En la capa gratuita cada modelo tiene su propio cupo diario, y cada pregunta gasta 2 o más "
               "consultas. Los cupos y los modelos disponibles cambian con el tiempo.")
    if clave:
        st.caption(f"Clave de Gemini cargada desde {origen}.")
    else:
        clave = st.text_input(
            "API key de Google AI Studio",
            type="password",
            key="agente_clave",
            help="Solo se usa en esta sesión y no se guarda. Para dejarla fija, consulta el README.",
        ).strip()
        st.caption("Crea una clave gratis en https://aistudio.google.com/apikey")

if not clave:
    st.warning(":material/key: Falta la API key de Gemini. Pégala arriba o configúrala en los secretos "
               "(ver el README).")
    st.stop()
if not modelo:
    st.warning(":material/warning: Escribe el nombre del modelo.")
    st.stop()

# La conversación se reinicia si cambia el archivo, el modelo o la clave.
firma = (uploaded_file.name, uploaded_file.size, modelo, agente.firma_clave(clave))
if st.session_state.get("agente_firma") != firma:
    st.session_state["agente_firma"] = firma
    st.session_state["agente_mensajes"] = []
    try:
        conversacion = agente.Conversacion(agente.crear_cliente(clave), df, modelo)
    except Exception as e:
        st.error(f":material/cancel: No se pudo iniciar el asistente: {agente.traducir_error(e)}")
        st.stop()
    st.session_state["agente_chat"] = conversacion

conversacion = st.session_state["agente_chat"]
mensajes = st.session_state["agente_mensajes"]


def mostrar(mensaje: dict):
    """Dibuja un mensaje de la conversación."""
    if mensaje["rol"] == "usuario":
        with st.chat_message("user", avatar=AVATAR_USUARIO):
            md('<span class="msg-usuario"></span>', unsafe_allow_html=True)  # marca para colorear la burbuja
            st.write(mensaje["texto"])
    else:
        with st.chat_message("assistant", avatar=AVATAR_AGENTE):
            if mensaje["rol"] == "error":
                st.error(f":material/cancel: {mensaje['texto']}")
            else:
                st.write(mensaje["texto"])
                st.caption(f"Modelo usado: {mensaje.get('modelo', '')}")


espacio_nueva = st.empty()  # el botón se dibuja al final, cuando ya se sabe si hay mensajes

for mensaje in mensajes:
    mostrar(mensaje)

# Sugerencias para quien no sabe qué preguntar (solo mientras la conversación está vacía)
sugerida = None
espacio_sugerencias = st.empty()
if not mensajes:
    with espacio_sugerencias.container():
        st.caption("Puedes empezar con una de estas preguntas, o escribir la tuya abajo:")
        for i, texto in enumerate(SUGERENCIAS):
            if st.button(texto, key=f"agente_sugerencia_{i}"):
                sugerida = texto

pregunta = st.chat_input("Escribe tu pregunta sobre los datos…") or sugerida

if pregunta and pregunta.strip():
    pregunta = pregunta.strip()
    espacio_sugerencias.empty()
    nuevo_usuario = {"rol": "usuario", "texto": pregunta}
    mostrar(nuevo_usuario)
    mensajes.append(nuevo_usuario)
    with st.chat_message("assistant", avatar=AVATAR_AGENTE):
        try:
            with st.spinner("Gemini está analizando tus datos…"):
                respuesta, _pasos, modelo_usado = conversacion.preguntar(pregunta)
            nuevo = {"rol": "agente", "texto": respuesta, "modelo": modelo_usado}
            st.write(respuesta)
            st.caption(f"Modelo usado: {modelo_usado}")
        except agente.ErrorAgente as e:
            nuevo = {"rol": "error", "texto": str(e)}
            st.error(f":material/cancel: {e}")
    mensajes.append(nuevo)

if mensajes and espacio_nueva.button(":material/delete: Nueva conversación", key="agente_nueva"):
    st.session_state["agente_mensajes"] = []
    st.session_state.pop("agente_firma", None)  # también reinicia la memoria del agente
    st.rerun()
