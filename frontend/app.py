"""Runbook Guardian — Frontend Streamlit.

Interfaz web para consultar el agente on-call.
Muestra resultados con evidencia visible, warnings de seguridad,
fuentes rechazadas y metadata de la respuesta.
"""

import requests
import streamlit as st

# --- Configuración ---
BACKEND_URL = "http://localhost:8000"
API_QUERY_URL = f"{BACKEND_URL}/api/v1/query"
API_HEALTH_URL = f"{BACKEND_URL}/api/v1/health"

# --- Page Config ---
st.set_page_config(
    page_title="Runbook Guardian",
    page_icon="🛡️",
    layout="wide",
)

# --- Header ---
st.title("🛡️ Runbook Guardian")
st.markdown(
    "Asistente seguro para equipos on-call — responde exclusivamente "
    "con evidencia de runbooks versionados."
)

# --- Sidebar: Estado del sistema ---
with st.sidebar:
    st.header("Estado del sistema")
    try:
        health = requests.get(API_HEALTH_URL, timeout=5).json()
        st.success(f"Backend: {health['status']}")
        st.metric("Runbooks indexados", health["runbooks_indexed"])
        st.caption(f"Versión: {health['version']}")
    except requests.exceptions.ConnectionError:
        st.error("Backend no disponible")
        st.caption(f"Verifica que el backend esté corriendo en {BACKEND_URL}")
    except Exception as e:
        st.warning(f"Error: {str(e)[:100]}")

    st.divider()
    st.markdown("**Restricciones de seguridad:**")
    st.markdown("- No ejecuta comandos")
    st.markdown("- No modifica infraestructura")
    st.markdown("- Requiere validación humana")

# --- Input de consulta ---
st.divider()

query = st.text_input(
    "Describe el incidente o síntoma",
    placeholder="Ej: El servicio nginx no responde, ¿qué hago?",
    max_chars=500,
    help="Máximo 500 caracteres. El sistema buscará en los runbooks indexados.",
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
    submit = st.button("🔍 Consultar", type="primary", use_container_width=True)

# --- Procesar consulta ---
if submit and query:
    with st.spinner("Buscando en runbooks..."):
        try:
            response = requests.post(
                API_QUERY_URL,
                json={"query": query},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            st.error(
                "No se pudo conectar con el backend. "
                f"Verifica que esté corriendo en {BACKEND_URL}"
            )
            st.stop()
        except requests.exceptions.Timeout:
            st.error("La consulta tardó demasiado. Intenta de nuevo.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"Error del servidor: {e.response.status_code}")
            st.stop()
        except Exception as e:
            st.error(f"Error inesperado: {str(e)[:200]}")
            st.stop()

    # --- Banner de modo fallback ---
    if data["metadata"]["mode"] == "fallback":
        st.warning(
            "⚠️ **Modo de respaldo activo** — El sistema de búsqueda semántica "
            "no está disponible. Los resultados pueden ser limitados.",
            icon="⚠️",
        )

    # --- Resultados ---
    results = data.get("results", [])

    if results:
        st.subheader(f"📄 {len(results)} resultado(s) encontrado(s)")

        for i, result in enumerate(results, 1):
            # Determinar si tiene warnings
            has_warning = len(result.get("warnings", [])) > 0
            border_color = "red" if has_warning else "green"

            with st.container(border=True):
                # Header del resultado
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(f"**Resultado {i}** — Sección: _{result['section']}_")
                with cols[1]:
                    score = result["similarity_score"]
                    if score > 0:
                        st.metric("Score", f"{score:.2f}")

                # Warnings de seguridad
                if has_warning:
                    for warning in result["warnings"]:
                        st.error(f"⚠️ **ADVERTENCIA:** {warning}", icon="🚨")

                # Contenido del fragmento
                st.code(result["text"], language="text")

                # Metadata del resultado
                meta_cols = st.columns(4)
                with meta_cols[0]:
                    st.caption(f"📁 {result['source_file']}")
                with meta_cols[1]:
                    st.caption(f"🏷️ v{result['version']}")
                with meta_cols[2]:
                    st.caption(f"📅 {result['last_reviewed']}")
                with meta_cols[3]:
                    if score > 0:
                        st.caption(f"📊 {score:.3f}")
    else:
        st.info(
            "No se encontró documentación relevante para esta consulta. "
            "Intente reformular con otros términos."
        )

    # --- Fuentes rechazadas ---
    rejected = data.get("rejected_sources", [])
    if rejected:
        with st.expander(f"🚫 Fuentes rechazadas ({len(rejected)})", expanded=False):
            for rej in rejected:
                st.markdown(f"- **{rej['source_file']}**: {rej['reason']}")

    # --- Warnings globales ---
    global_warnings = data.get("warnings", [])
    if global_warnings:
        for warning in global_warnings:
            if "fallback" not in warning.lower():
                st.warning(warning, icon="⚠️")

    # --- Metadata de respuesta ---
    st.divider()
    meta = data["metadata"]
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.caption(f"⏱️ Respuesta en {meta['response_time_ms']}ms")
    with meta_cols[1]:
        st.caption(f"📚 {meta['total_candidates']} candidatos evaluados")
    with meta_cols[2]:
        st.caption(f"🔧 Modo: {meta['mode']}")

elif submit and not query:
    st.warning("Por favor, escribe una consulta antes de buscar.")
