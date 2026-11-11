import streamlit as st

from ui import md, icon, inject_css, page_header, tool_card

# ── Configuración de página y estilos (primero, para que no se vea sin diseño al cargar)
st.set_page_config(
    page_title="Portal Contable",
    page_icon=":material/apartment:",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_css()

import time

from sesion import crear_autenticador, restaurar_sesion


# ── Sesión ───────────────────────────────────────────────────────────────────
# Las credenciales vienen de st.secrets (en Streamlit Cloud: App Settings > Secrets).
# Si la sesión se perdió (recarga, pestaña nueva), se recupera de la cookie.
restaurar_sesion()
authenticator = crear_autenticador()

# ── Pantalla de Login ─────────────────────────────────────────────────────────
if not st.session_state.get("authentication_status"):
    _, centro, _ = st.columns([1, 1.15, 1])
    with centro:
        md(f"""
        <div class="brand">
            <div class="brand-icon">{icon("building", 30)}</div>
            <div class="brand-name">Portal Contable</div>
            <div class="brand-sub">Ingrese sus credenciales para continuar</div>
        </div>
        """, unsafe_allow_html=True)
        authenticator.login(location="main", key="login_portal")
    if st.session_state.get("authentication_status"):
        # El login guarda la cookie con un componente del navegador: se le da un
        # instante para que la escriba antes de redibujar la página sin el login.
        time.sleep(1.2)
        st.rerun()
else:
    authenticator.login(location="main", key="login_portal")

auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    _, centro, _ = st.columns([1, 1.15, 1])
    with centro:
        st.error(":material/cancel: Usuario o contraseña incorrectos.")
    st.stop()

elif auth_status is None:
    st.stop()

# ── Usuario autenticado: mostrar app ─────────────────────────────────────────
# Botón de logout en sidebar
with st.sidebar:
    md(
        f'<div class="user-chip">{icon("user", 18)}<span>{st.session_state.get("name", "")}</span></div>',
        unsafe_allow_html=True,
    )
    authenticator.logout("Cerrar sesión", location="sidebar", key="logout_sidebar")
    st.divider()

# ── Contenido Principal ───────────────────────────────────────────────────────
page_header(
    "Automatización y Conciliación Contable",
    "Portal centralizado para la validación de extractos bancarios, conciliación de IVA en "
    "facturación electrónica y preparación de traslados de nómina. Seleccione una herramienta "
    "para comenzar.",
    "building",
)

md('<div class="section-title">Herramientas</div>', unsafe_allow_html=True)

HERRAMIENTAS = [
    {
        "titulo": "Comparativa Contable",
        "desc": "Audita las transacciones bancarias cruzando automáticamente los valores del "
                "extracto (CSV) contra los registros de débitos y créditos en el libro contable (Excel).",
        "chips": ["CSV Bancario", "Excel Contable", "Tolerancias"],
        "icono": "search", "tono": "blue", "pagina": "pages/1_Comparativa_Contable.py",
    },
    {
        "titulo": "Comparativa de IVA",
        "desc": "Verifique rápida y confiablemente que el NIT Emisor, el Nombre y el IVA reportado "
                "en el reporte de Facturación Electrónica coincidan exactamente con el Libro Auxiliar.",
        "chips": ["NIT Validación", "Reportes DIAN"],
        "icono": "receipt", "tono": "green", "pagina": "pages/2_Comparativa_IVA.py",
    },
    {
        "titulo": "Traslado de Nómina",
        "desc": "Agiliza la preparación de la interfaz de nómina. Traspasa conceptos y valores desde "
                "el reporte crudo (3.3) hacia la plantilla formateada (3.2) y genera la hoja SIIGO.",
        "chips": ["Mapeo Dinámico", "Deduplicación", "SIIGO"],
        "icono": "clipboard-list", "tono": "amber", "pagina": "pages/3_Traslado_Nomina.py",
    },
    {
        "titulo": "Anexo ERI y ESF",
        "desc": "Genera los anexos al Estado de Resultados Integral y al Estado de Situación "
                "Financiera desde la hoja terceros_ del archivo EEFF, con métricas y gráficos interactivos.",
        "chips": ["Ingresos / Gastos", "Pivote Mensual", "Plotly"],
        "icono": "bar-chart", "tono": "purple", "pagina": "pages/4_ESF_ERI.py",
    },
    {
        "titulo": "Agente de Datos",
        "desc": "Analiza archivos Excel y CSV con lenguaje natural y un asistente de IA para explorar "
                "datos, generar estadísticas y obtener respuestas sobre la información.",
        "chips": ["OpenAI GPT", "CSV / Excel", "Análisis IA"],
        "icono": "bot", "tono": "navy", "pagina": "pages/5_Agente de datos.py",
    },
]

for inicio in range(0, len(HERRAMIENTAS), 3):
    columnas = st.columns(3, gap="medium")
    for col, h in zip(columnas, HERRAMIENTAS[inicio:inicio + 3]):
        with col:
            with st.container(border=True):
                tool_card(h["titulo"], h["desc"], h["chips"], h["icono"], h["tono"])
                st.page_link(h["pagina"], label="Abrir herramienta", icon=":material/arrow_forward:")
    st.write("")

md('<div class="page-footer">Gestión Contable Inteligente v2.1 · Diseñado para precisión y ahorro de tiempo operativo</div>',
   unsafe_allow_html=True)
