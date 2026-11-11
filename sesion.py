"""Sesión del portal: crea el autenticador y recupera la sesión desde la cookie.

La sesión de Streamlit se pierde al recargar la página, abrir una pestaña nueva o
reconectarse. Por eso, además de guardar la cookie al iniciar sesión (lo hace
streamlit-authenticator), todas las páginas la leen para volver a entrar solas.
"""
from datetime import datetime

import jwt
import streamlit as st
import streamlit_authenticator as stauth


def _configuracion():
    """Credenciales y cookie, leídas de st.secrets (igual que en Streamlit Cloud)."""
    credenciales = {"usernames": {}}
    for usuario, datos in st.secrets.get("credentials", {}).items():
        credenciales["usernames"][usuario] = {
            "name": datos["name"],
            "password": datos["password"],  # debe ser hash bcrypt
            "email": datos.get("email", ""),
        }
    cookie = st.secrets.get("cookie", {
        "name": "portal_contable_auth",
        "key": "clave_secreta_cambiar",
        "expiry_days": 1,
    })
    return credenciales, cookie


def crear_autenticador():
    credenciales, cookie = _configuracion()
    return stauth.Authenticate(
        credenciales, cookie["name"], cookie["key"], cookie["expiry_days"],
    )


def restaurar_sesion() -> bool:
    """Devuelve True si hay sesión activa; si se perdió, la recupera de la cookie firmada."""
    if st.session_state.get("authentication_status"):
        return True
    if st.session_state.get("logout"):  # cerró sesión a propósito
        return False

    credenciales, cookie = _configuracion()
    try:
        token = st.context.cookies.get(cookie["name"])
    except Exception:
        return False
    if not token:
        return False
    try:
        datos = jwt.decode(token, cookie["key"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return False

    usuario = datos.get("username")
    vigente = datos.get("exp_date", 0) > datetime.now().timestamp()
    if not vigente or usuario not in credenciales["usernames"]:
        return False

    st.session_state["username"] = usuario
    st.session_state["name"] = credenciales["usernames"][usuario]["name"]
    st.session_state["authentication_status"] = True
    return True


def requerir_sesion():
    """Guardia de las páginas: si no hay sesión (ni cookie válida), avisa y detiene la página."""
    if restaurar_sesion():
        return
    st.warning(":material/warning: Debe iniciar sesión primero.")
    st.page_link("Inicio.py", label="Ir al login", icon=":material/lock:")
    st.stop()
