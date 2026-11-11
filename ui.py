"""Estilos compartidos y componentes de interfaz del portal contable."""
import json
import re
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

# ── Iconos (trazo de 24x24, estilo Lucide) ────────────────────────────────────
_ICONS = {
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
    "clipboard-list": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    "bar-chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "pie-chart": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    "bot": '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    "settings": '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "x-circle": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "landmark": '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "folder-open": '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/>',
    "eye": '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "table": '<path d="M12 3v18"/><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/>',
}

_TOKEN = re.compile(r"\[\[([a-z0-9-]+)\]\]")


def icon(name: str, size: int = 18) -> str:
    """SVG en línea del icono `name`; hereda el color del texto."""
    cuerpo = _ICONS[name]
    return (
        f'<svg class="ic" xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{cuerpo}</svg>'
    )


def render_icons(html: str) -> str:
    """Reemplaza los marcadores [[nombre]] por su SVG."""
    return _TOKEN.sub(lambda m: icon(m.group(1)), html)


def md(body: str, unsafe_allow_html: bool = False, **kwargs):
    """st.markdown que además resuelve los marcadores [[icono]] en HTML."""
    if unsafe_allow_html:
        body = render_icons(body)
    st.markdown(body, unsafe_allow_html=unsafe_allow_html, **kwargs)


_DARK_VARS = '''        --bg: #0A101C;    --surface: #111A2B;   --surface-2: #17233C;  --border: #23324D;
        --text: #E7EDF7;  --muted: #98A6BD;     --heading: #F2F6FC;
        --brand: #5B9BFF; --brand-strong: #86B6FF; --brand-soft: rgba(91, 155, 255, .15);
        --green: #4ADE80; --green-soft: rgba(74, 222, 128, .13);
        --amber: #FBBF24; --amber-soft: rgba(251, 191, 36, .14);
        --red: #F87171;   --red-soft: rgba(248, 113, 113, .14);
        --purple: #B79CFF; --purple-soft: rgba(183, 156, 255, .15);
        --btn: #2F6BFF;   --btn-hover: #4F82FF;
        --glow: rgba(91, 155, 255, .14);
        --shadow: 0 1px 2px rgba(0, 0, 0, .35), 0 10px 28px rgba(0, 0, 0, .35);'''


# ── Hoja de estilos ───────────────────────────────────────────────────────────
# Variables para modo claro y oscuro: el modo oscuro sigue la preferencia del
# sistema (igual que el tema de Streamlit, que no está fijado en config.toml).
_CSS = """
:root {
    --bg: #F5F7FB;        --surface: #FFFFFF;   --surface-2: #F0F4FA;  --border: #E3E8F1;
    --text: #0F172A;      --muted: #64748B;     --heading: #0B1B3A;
    --brand: #2563EB;     --brand-strong: #1D4ED8;  --brand-soft: #E8F0FF;
    --green: #15803D;     --green-soft: #E7F6EC;
    --amber: #B45309;     --amber-soft: #FFF1DC;
    --red: #B42318;       --red-soft: #FDECEA;
    --purple: #6D28D9;    --purple-soft: #F1EAFE;
    --btn: #0B1B3A;       --btn-hover: #1E3A8A;
    --glow: rgba(37, 99, 235, .10);
    --shadow: 0 1px 2px rgba(15, 23, 42, .05), 0 10px 28px rgba(15, 23, 42, .06);
    --radius: 16px;
}
:root[data-theme="dark"] {
__DARK__
}
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
__DARK__
    }
}

/* Base ---------------------------------------------------------------------- */
.stApp {
    background: radial-gradient(900px 420px at 92% -8%, var(--glow), transparent 65%), var(--bg);
    color: var(--text);
}
html, body, .stApp, p, li, label, h1, h2, h3, h4, h5, h6, input, textarea, button, td, th {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}
.stApp p, .stApp li, .stApp label { color: var(--text); }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1280px; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
.ic { vertical-align: -0.18em; flex: none; }
[data-testid="stCaptionContainer"], .stApp small { color: var(--muted) !important; }

/* Barra lateral ------------------------------------------------------------- */
[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
[data-testid="stSidebarNav"]::before {
    content: "Portal Contable"; display: block; font-weight: 800; font-size: 1.05rem;
    letter-spacing: -.01em; color: var(--heading); padding: 20px 16px 16px 62px; margin: 0 0 6px;
    background: __BRAND_ICON__ no-repeat 16px center / 34px 34px;
}
[data-testid="stSidebarNav"] a {
    display: flex; align-items: center; gap: 10px; border-radius: 12px;
    padding: .5rem .8rem; margin: 2px 8px; font-weight: 500; color: var(--muted);
}
[data-testid="stSidebarNav"] a span { color: inherit; }
[data-testid="stSidebarNav"] a::before {
    content: ""; width: 18px; height: 18px; flex: none; background-color: currentColor; opacity: .85;
    -webkit-mask: var(--nav-ic) center / contain no-repeat; mask: var(--nav-ic) center / contain no-repeat;
}
[data-testid="stSidebarNav"] a:hover { background: var(--surface-2); color: var(--heading); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--brand-soft); color: var(--brand); font-weight: 700; }
__NAV_ICONS__

/* Encabezado de página ------------------------------------------------------ */
.hero, .header-block {
    position: relative; overflow: hidden; display: flex; align-items: center; gap: 20px;
    background: linear-gradient(125deg, #0B1B3A 0%, #17338A 55%, #2563EB 100%);
    border-radius: 20px; padding: 28px 34px; margin-bottom: 28px; color: #fff;
    box-shadow: 0 14px 34px rgba(11, 27, 58, .22);
}
.hero::after {
    content: ""; position: absolute; right: -60px; top: -90px; width: 280px; height: 280px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 255, 255, .22), transparent 65%); pointer-events: none;
}
.hero .hero-icon {
    width: 56px; height: 56px; border-radius: 16px; flex: none; z-index: 1;
    background: rgba(255, 255, 255, .14); border: 1px solid rgba(255, 255, 255, .22);
    display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);
}
.hero > div:last-child { z-index: 1; }
.hero .eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: rgba(255, 255, 255, .7); margin-bottom: 4px; }
.hero h1, .header-block h1 { margin: 0; padding: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; color: #fff !important; }
.hero p, .header-block p { margin: 6px 0 0; font-size: .95rem; line-height: 1.55; color: rgba(255, 255, 255, .86) !important; }
.hero b, .hero strong { color: #fff; }

/* Títulos de sección -------------------------------------------------------- */
.section-title {
    display: flex; align-items: center; gap: 10px; margin: 8px 0 14px; padding-bottom: 10px;
    font-size: 1.02rem; font-weight: 700; color: var(--heading); border-bottom: 1px solid var(--border);
}
.section-title .ic { color: var(--brand); }
.tab-header { font-size: 1.05rem; font-weight: 700; color: var(--heading); margin-bottom: 6px; }

/* Los contenedores HTML de las páginas no envuelven a los widgets de Streamlit,
   por eso no llevan caja propia. */
.upload-section, .result-block, .bloque-box, .bloque-box-sn { background: transparent; box-shadow: none; border: 0; padding: 0; margin: 0; }

/* Tarjetas de métricas ------------------------------------------------------ */
.metric-card {
    --tone: var(--brand); position: relative; overflow: hidden; height: 100%; text-align: left;
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 18px 20px; box-shadow: var(--shadow);
}
.metric-card:has(.green)  { --tone: var(--green); }
.metric-card:has(.red)    { --tone: var(--red); }
.metric-card:has(.orange) { --tone: var(--amber); }
.metric-card:has(.purple) { --tone: var(--purple); }
.metric-card::before { content: ""; display: block; width: 28px; height: 4px; border-radius: 4px; background: var(--tone); margin-bottom: 14px; }
.metric-card::after {
    content: ""; position: absolute; right: -30px; top: -30px; width: 110px; height: 110px; border-radius: 50%;
    background: radial-gradient(circle, color-mix(in srgb, var(--tone) 18%, transparent), transparent 70%); pointer-events: none;
}
.metric-card .number { font-size: 1.85rem; font-weight: 800; line-height: 1.1; letter-spacing: -.02em; }
.metric-card .label { min-height: 2.5em; margin-top: 7px; font-size: .7rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }
.green { color: var(--green); } .red { color: var(--red); } .blue { color: var(--brand); }
.orange { color: var(--amber); } .purple { color: var(--purple); }

/* Avisos propios ------------------------------------------------------------ */
.warn-box, .info-box { border-radius: 12px; padding: 12px 16px; margin: 10px 0; font-size: .88rem; border: 1px solid var(--border); }
.warn-box { background: var(--amber-soft); color: var(--amber); }
.info-box { background: var(--brand-soft); color: var(--brand); }
.pdf-badge {
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px;
    background: var(--purple-soft); color: var(--purple); font-size: .78rem; font-weight: 600;
}

/* Estado vacío -------------------------------------------------------------- */
.empty-state { text-align: center; padding: 56px 20px; color: var(--muted); }
.empty-state .empty-icon {
    width: 76px; height: 76px; margin: 0 auto 18px; border-radius: 22px;
    background: var(--brand-soft); color: var(--brand); display: flex; align-items: center; justify-content: center;
}
.empty-state .empty-title { font-size: 1.1rem; font-weight: 700; color: var(--heading); margin: 0 0 6px; }
.empty-state .empty-sub { font-size: .92rem; margin: 0 auto; max-width: 620px; line-height: 1.6; color: var(--muted); }

/* Widgets de Streamlit ------------------------------------------------------ */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface); border: 1.5px dashed var(--border); border-radius: 14px; padding: 1.2rem; transition: .15s;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--brand); background: var(--brand-soft); }
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--text) !important; font-weight: 600; }
[data-testid="stFileUploaderDropzoneInstructions"] small { color: var(--muted) !important; }

.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 12px; font-weight: 600; padding: .55rem 1.15rem; transition: .15s;
    background: var(--surface); color: var(--heading); border: 1px solid var(--border);
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--brand); color: var(--brand); }
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] > button {
    background: var(--btn); color: #fff; border-color: var(--btn);
}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover { background: var(--btn-hover); border-color: var(--btn-hover); color: #fff; }

/* El texto de los botones hereda su color (la regla general de párrafos lo dejaba oscuro sobre azul) */
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: inherit !important; }
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p,
[data-testid="stFormSubmitButton"] > button p { color: #fff !important; }

[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
    border-radius: 12px !important; background: var(--surface) !important;
}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] { border: 1px solid var(--border) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: var(--brand) !important; box-shadow: 0 0 0 3px var(--brand-soft);
}
input, textarea { color: var(--text) !important; }

[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; box-shadow: var(--shadow); }
[data-testid="stExpander"] summary { font-weight: 600; color: var(--heading); }

.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { padding: 10px 16px; font-weight: 600; color: var(--muted); }
.stTabs [aria-selected="true"] { color: var(--brand); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--brand); height: 3px; border-radius: 3px; }

/* Color de acento de radios, casillas e interruptores (sin tema fijo en config.toml) */
label[data-baseweb="radio"]:has(input:checked) > div:first-child { background-color: var(--brand) !important; border-color: var(--brand) !important; }
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child,
label[data-baseweb="checkbox"]:has(input:checked) > div:first-child { background-color: var(--brand) !important; border-color: var(--brand) !important; }
[data-baseweb="slider"] div[role="slider"] { background-color: var(--brand) !important; }
[data-baseweb="progress-bar"] > div > div { background-color: var(--brand) !important; }

/* Chat ---------------------------------------------------------------------- */
[data-testid="stChatMessage"] {
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 14px 18px; box-shadow: var(--shadow);
}
[data-testid="stChatMessage"]:has(.msg-usuario) { background: var(--brand-soft); border-color: transparent; }
[data-testid="stElementContainer"]:has(.msg-usuario) { display: none; }
[data-testid="stChatMessage"] p { margin-bottom: .35rem; }
[data-testid="stChatInput"] { border-radius: 16px; border: 1px solid var(--border); background: var(--surface); box-shadow: var(--shadow); }
[data-testid="stChatInput"]:focus-within { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-soft); }
[data-testid="stChatInput"] textarea { background: transparent !important; }
[data-testid="stBottom"] > div { background: var(--bg); }

/* Indicador de carga: una sola animación, con los colores del portal */
[data-testid="stSpinner"] { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 12px;
    background: var(--brand-soft); color: var(--brand); font-weight: 600; }
[data-testid="stSpinner"] p { color: inherit !important; margin: 0; }
[data-testid="stSpinner"] i, [data-testid="stSpinner"] > div:first-child { border-color: var(--brand) transparent var(--brand) var(--brand) !important; }

[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 14px; }
[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 18px; box-shadow: var(--shadow); }
[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 1.7rem 1.6rem 1.3rem; box-shadow: var(--shadow); }
hr { border-color: var(--border); }
a { color: var(--brand); }

/* Tarjetas de herramientas (inicio) ---------------------------------------- */
/* La caja de la tarjeta es el contenedor con borde de Streamlit: así el enlace queda dentro. */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] .tool-card) {
    background: var(--surface); border: 1px solid var(--border) !important; border-radius: 20px !important;
    padding: 8px 8px 6px; box-shadow: var(--shadow); transition: .2s;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] .tool-card):hover {
    border-color: var(--brand) !important; box-shadow: 0 16px 36px var(--glow);
}
.tool-card { padding: 16px 16px 14px; min-height: 318px; }
[data-testid="stPageLink"] { width: 100%; }
/* Enlace "Abrir herramienta": pie discreto de la tarjeta, sin caja propia */
[data-testid="stPageLink"] a {
    width: 100%; box-sizing: border-box; background: transparent;
    display: flex; flex-direction: row-reverse; align-items: center; justify-content: space-between; gap: 8px;
    margin: 0 16px; width: calc(100% - 32px); padding: .7rem 0 .55rem; border-top: 1px solid var(--border);
    border-radius: 0; font-size: .9rem; font-weight: 600; text-decoration: none; color: var(--brand); transition: .15s;
}
[data-testid="stPageLink"] a * { color: inherit !important; }
[data-testid="stPageLink"] a:hover { color: var(--brand-strong); background: transparent; padding-left: 4px; }
.tool-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.tool-icon.blue   { background: var(--brand-soft);  color: var(--brand); }
.tool-icon.green  { background: var(--green-soft);  color: var(--green); }
.tool-icon.amber  { background: var(--amber-soft);  color: var(--amber); }
.tool-icon.purple { background: var(--purple-soft); color: var(--purple); }
.tool-icon.navy   { background: var(--surface-2);   color: var(--heading); }
.tool-title { font-size: 1.08rem; font-weight: 700; color: var(--heading); margin-bottom: 8px; }
.tool-desc  { font-size: .9rem; line-height: 1.6; color: var(--muted); margin-bottom: 14px; min-height: 140px; }
.chip {
    display: inline-block; margin: 2px 4px 2px 0; padding: 3px 11px; border-radius: 999px;
    background: var(--surface-2); border: 1px solid var(--border); color: var(--muted); font-size: .72rem; font-weight: 600;
}
.brand { text-align: center; padding: 28px 0 14px; }
.brand .brand-icon {
    width: 68px; height: 68px; margin: 0 auto 16px; border-radius: 20px; color: #fff;
    background: linear-gradient(135deg, #0B1B3A, #2563EB);
    display: flex; align-items: center; justify-content: center; box-shadow: 0 14px 30px rgba(37, 99, 235, .35);
}
.brand .brand-name { font-size: 1.75rem; font-weight: 800; color: var(--heading); letter-spacing: -.02em; }
.brand .brand-sub  { color: var(--muted); margin-top: 4px; font-size: .95rem; }
.user-chip {
    display: flex; align-items: center; gap: 10px; padding: 10px 12px; margin-bottom: 8px;
    background: var(--surface-2); border-radius: 12px; font-weight: 600; color: var(--heading);
}
.page-footer { margin-top: 48px; padding-top: 18px; text-align: center; color: var(--muted); font-size: .82rem; border-top: 1px solid var(--border); }
"""


def _data_uri(svg_body: str, color: str = "black") -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="'
        + color + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        + svg_body + "</svg>"
    )
    return 'url("data:image/svg+xml;utf8,' + quote(svg, safe="/:=,;() ") + '")'


# Icono de cada página en el menú lateral (mismo orden que los archivos de pages/)
_NAV_ORDER = ["building", "search", "receipt", "clipboard-list", "bar-chart", "bot", "search"]


def _estilos() -> str:
    marca = (
        'url("data:image/svg+xml;utf8,' + quote(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 34 34">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#0B1B3A"/><stop offset="1" stop-color="#2563EB"/></linearGradient></defs>'
            '<rect width="34" height="34" rx="10" fill="url(#g)"/>'
            '<g transform="translate(7 7)" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">' + _ICONS["building"] + "</g></svg>", safe="/:=,;() ") + '")'
    )
    nav = "\n".join(
        f'[data-testid="stSidebarNav"] li:nth-child({i}) a {{ --nav-ic: {_data_uri(_ICONS[n])}; }}'
        for i, n in enumerate(_NAV_ORDER, start=1)
    )
    return (_CSS.replace("__DARK__", _DARK_VARS).replace("__BRAND_ICON__", marca)
            .replace("__NAV_ICONS__", nav))


# ── Botón de modo claro / oscuro ──────────────────────────────────────────────
# Streamlit guarda el tema elegido en localStorage (una clave por ruta); el botón
# escribe esa clave, recuerda la elección en 'portalTheme' y recarga. El atributo data-theme hace que los estilos propios sigan la misma elección.
_THEME_HTML = """
<style>
    html, body { margin: 0; background: transparent; }
    button {
        width: 100%; display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer;
        border-radius: 12px; border: 1px solid; font: 600 14px Inter, 'Segoe UI', system-ui, sans-serif;
    }
    svg { flex: none; }
</style>
<button id="t" type="button"></button>
<script>
(function () {
    const P = window.parent, D = P.document;
    // Streamlit guarda el tema por ruta: stActiveTheme-<ruta>-v1 con name "Light" o "Dark".
    const KEY = 'stActiveTheme-' + P.location.pathname + '-v1', PREF = 'portalTheme';
    const SUN = '__SUN__', MOON = '__MOON__';
    // Los estilos también se guardan en el <head> del navegador: Streamlit borra los que
    // vienen con cada página al navegar, y así no hay un instante sin diseño.
    const CSS = __CSS__;
    let hoja = D.getElementById('portal-css');
    if (!hoja) { hoja = D.createElement('style'); hoja.id = 'portal-css'; D.head.appendChild(hoja); }
    if (hoja.textContent !== CSS) hoja.textContent = CSS;
    const sistema = P.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    let pref = null;
    try { pref = P.localStorage.getItem(PREF); } catch (e) {}
    function guardar(m) { P.localStorage.setItem(KEY, JSON.stringify({ name: m === 'dark' ? 'Dark' : 'Light' })); }

    if (pref) {
        let actual = null;
        try { actual = (JSON.parse(P.localStorage.getItem(KEY)) || {}).name; } catch (e) {}
        const desfasado = actual ? actual.toLowerCase() !== pref : pref !== sistema;
        if (desfasado && !P.sessionStorage.getItem('portalThemeReload')) {
            guardar(pref);
            P.sessionStorage.setItem('portalThemeReload', '1');
            P.location.reload();
            return;
        }
        if (!desfasado) P.sessionStorage.removeItem('portalThemeReload');
    }

    const modo = pref || sistema;
    D.documentElement.setAttribute('data-theme', modo);
    const css = P.getComputedStyle(D.documentElement);
    const v = (n, d) => css.getPropertyValue(n).trim() || d;
    const b = document.getElementById('t');
    b.style.background = v('--surface-2', '#F0F4FA');
    b.style.color = v('--heading', '#0B1B3A');
    b.style.borderColor = v('--border', '#E3E8F1');
    b.innerHTML = (modo === 'dark' ? SUN : MOON) + '<span>' + (modo === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro') + '</span>';
    b.onclick = function () {
        const sig = modo === 'dark' ? 'light' : 'dark';
        P.localStorage.setItem(PREF, sig);
        guardar(sig);
        P.sessionStorage.removeItem('portalThemeReload');
        P.location.reload();
    };
})();
</script>
"""


def theme_toggle():
    """Botón de la barra lateral que alterna entre modo claro y oscuro."""
    def _svg(cuerpo):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                + cuerpo + "</svg>")
    html = (_THEME_HTML.replace("__SUN__", _svg(_ICONS["sun"])).replace("__MOON__", _svg(_ICONS["moon"]))
            .replace("__CSS__", json.dumps(_FUENTE_CSS + _estilos())))
    with st.sidebar:
        components.html(html, height=48)


# La fuente va en su propio bloque: si la descarga de Google Fonts es lenta, no retrasa el resto de los estilos.
_FUENTE_CSS = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"
_FUENTE = _FUENTE_CSS


def inject_css():
    """Aplica la hoja de estilos del portal a la página actual."""
    # Cada <style> empieza en su propia línea: Markdown solo lo toma como HTML así.
    st.markdown(f"<style>{_FUENTE}</style>\n<style>{_estilos()}</style>", unsafe_allow_html=True)
    theme_toggle()


# ── Componentes ───────────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon_name: str = "file-text"):
    """Encabezado de página con icono."""
    sub = f"<p>{render_icons(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="hero"><div class="hero-icon">{icon(icon_name, 26)}</div>'
        f'<div><div class="eyebrow">Portal Contable</div><h1>{title}</h1>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def section_title(text: str, icon_name: str = "file-text"):
    st.markdown(
        f'<div class="section-title">{icon(icon_name)}<span>{text}</span></div>',
        unsafe_allow_html=True,
    )


def metric_card(value, label: str, tone: str = "blue") -> str:
    """HTML de una tarjeta de métrica (tone: blue, green, red, orange, purple)."""
    return (
        f'<div class="metric-card"><div class="number {tone}">{value}</div>'
        f'<div class="label">{label}</div></div>'
    )


def tool_card(title: str, desc: str, chips, icon_name: str, tone: str = "blue"):
    """Tarjeta de una herramienta para la página de inicio."""
    fichas = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(
        f'<div class="tool-card"><div class="tool-icon {tone}">{icon(icon_name, 24)}</div>'
        f'<div class="tool-title">{title}</div><div class="tool-desc">{desc}</div>'
        f"<div>{fichas}</div></div>",
        unsafe_allow_html=True,
    )


def empty_state(title: str, subtitle: str = "", icon_name: str = "folder-open"):
    st.markdown(
        f'<div class="empty-state"><div class="empty-icon">{icon(icon_name, 32)}</div>'
        f'<p class="empty-title">{title}</p><p class="empty-sub">{render_icons(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )
