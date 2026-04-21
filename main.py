# =============================================================================
# main.py — Sistema de Mando Único | Alcalde Edward Infante
# Carmen de la Legua-Reynoso, Callao 2026
# =============================================================================

import streamlit as st
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y SEGURIDAD
# =============================================================================

st.set_page_config(
    page_title="Sistema de Mando · Alcalde Infante",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configurar Gemini desde st.secrets (NUNCA hardcodear la clave)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    GEMINI_OK = True
except Exception:
    GEMINI_OK = False
    st.sidebar.warning("⚠️ Configura GEMINI_API_KEY en tus secrets de Streamlit.")

# =============================================================================
# 2. ESTILOS CSS PERSONALIZADOS
# =============================================================================

st.markdown("""
<style>
    /* Tema oscuro político */
    .main { background-color: #050b14; }
    .block-container { padding-top: 1rem; }

    /* Tarjetas de métricas */
    .metric-card {
        background: linear-gradient(135deg, #0d1628, #111d35);
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val   { font-size: 2rem; font-weight: 800; color: #f97316; }
    .metric-label { font-size: 0.75rem; color: #64748b; letter-spacing: .08em; text-transform: uppercase; }

    /* Header principal */
    .main-header {
        background: linear-gradient(90deg, #0a1628 0%, #0f2040 100%);
        border-bottom: 2px solid #f97316;
        padding: 14px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .main-title   { color: #f8fafc; font-size: 1.4rem; font-weight: 800; margin: 0; }
    .main-sub     { color: #64748b; font-size: 0.75rem; letter-spacing: .12em; margin: 0; }

    /* Sección de incidencias */
    .incident-box {
        background: #0a1222;
        border-left: 3px solid #ef4444;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
    .incident-box.estable { border-left-color: #22c55e; }
    .incident-box.riesgo  { border-left-color: #eab308; }

    /* Ocultar footer de Streamlit */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. DATOS GEOGRÁFICOS — COORDENADAS EXACTAS DE CARMEN DE LA LEGUA
# =============================================================================

SECTORES = pd.DataFrame({
    "sector": [
        "Sector Reynoso (Jr. Puno/Callao)",
        "Sector Villa (El Pozo/Pacífico)",
        "Zona Alta (Sectores 13-15)",
        "Urb. 22 de Octubre",
        "Av. Julio C. Tello",
        "Jr. Independencia",
        "Jr. Mariano Melgar",
        "Av. 1° de Mayo",
        "Perú 5ta Zona",
        "Jr. Loreto",
    ],
    "lat": [
        -12.0435, -12.0415, -12.0378,
        -12.0450, -12.0420, -12.0440,
        -12.0460, -12.0480, -12.0520,
        -12.0445,
    ],
    "lon": [
        -77.0982, -77.1045, -77.0915,
        -77.0960, -77.0945, -77.0970,
        -77.0955, -77.0975, -77.0930,
        -77.0965,
    ],
    "estado": [
        "Crítico", "Estable", "Riesgo",
        "Estable", "Riesgo", "Crítico",
        "Estable", "Riesgo", "Crítico",
        "Estable",
    ],
    "incidencias": [14, 3, 8, 4, 7, 11, 2, 6, 13, 3],
    "descripcion": [
        "Alta incidencia de robos y desmonte acumulado",
        "Zona tranquila. Pendiente mejora de pistas",
        "Conflictos vecinales y alumbrado deficiente",
        "Necesita refuerzo de serenazgo nocturno",
        "Comercio ambulatorio sin control",
        "Pandillaje reportado por vecinos",
        "Sin problemas mayores reportados",
        "Baches críticos en tramo central",
        "Zona de alto riesgo. Patrullaje intensivo",
        "Vecinos satisfechos con limpieza pública",
    ],
})

# Paleta de colores por estado
COLOR_MAP = {"Crítico": "#ef4444", "Riesgo": "#eab308", "Estable": "#22c55e"}

# =============================================================================
# 4. DATOS DE SENTIMIENTO Y OPOSICIÓN
# =============================================================================

OPOSICION = {
    "Edith Quezada": {"presencia": 31, "tendencia": "▲ +3%", "color": "#a78bfa"},
    "Carlos Cox (Somos Perú)": {"presencia": 22, "tendencia": "▼ -1%", "color": "#38bdf8"},
    "Daniel Lecca (Ren. Popular)": {"presencia": 28, "tendencia": "▲ +5%", "color": "#f97316"},
}

SENTIMIENTO_GLOBAL = {
    "Aprobación Alcalde Infante": 38,
    "Satisfacción Programa LOGRA": 62,
    "Satisfacción Lonchecito": 71,
    "Percepción Seguridad": 29,
}

# =============================================================================
# 5. AGENTE GEMINI — COPYWRITER POLÍTICO
# =============================================================================

SYSTEM_PROMPT = """
Eres el Director de Comunicaciones del Alcalde Edwards Javier Infante López 
de Carmen de la Legua-Reynoso, Callao.

Tu misión: redactar respuestas políticas estratégicas a los comentarios 
de los vecinos del distrito.

Tono y estilo:
- "Chalaco elegante": cercano, directo, con orgullo del Callao pero sin vulgaridades.
- Empático y humano. Siempre validar el sentimiento del vecino antes de responder.
- Estratégico: cada respuesta debe destacar UNO de los logros reales del alcalde.
- Brevedad efectiva: máximo 4 párrafos cortos.
- Cierra siempre con un llamado a la acción o un dato concreto de gestión.

Programas reales que puedes mencionar:
- Programa LOGRA: capacitación técnico-laboral para jóvenes del distrito.
- Lonchecito: programa de alimentación para niños en edad escolar.
- Refuerzo de serenazgo con nuevas unidades.
- Mejora de infraestructura vial en sectores priorizados.

Nunca ataques directamente a la oposición. Responde con hechos y gestión.
Nunca inventes cifras que no se te hayan dado.
Formato de respuesta: texto plano, sin markdown, listo para publicar en redes sociales.
"""

def generar_respuesta_politica(comentario_vecino: str, contexto_sector: str = "") -> str:
    """
    Llama a Gemini 1.5 Flash con el system prompt del Director de Comunicaciones.
    Retorna la respuesta estratégica lista para publicar.
    """
    if not GEMINI_OK:
        return "❌ Error: Configura la clave GEMINI_API_KEY en st.secrets para activar el agente."

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )

        prompt_usuario = f"""
Comentario del vecino:
\"{comentario_vecino}\"

Contexto del sector (si aplica): {contexto_sector if contexto_sector else 'No especificado.'}

Genera la respuesta estratégica ahora.
"""
        response = model.generate_content(prompt_usuario)
        return response.text

    except Exception as e:
        return f"❌ Error al conectar con Gemini: {str(e)}"

# =============================================================================
# 6. INTERFAZ PRINCIPAL
# =============================================================================

# --- Header ---
st.markdown("""
<div class="main-header">
    <p class="main-title">🏛️ Sistema de Mando Único — Alcalde Edwards Infante López</p>
    <p class="main-sub">Carmen de la Legua-Reynoso · Callao · Panel Estratégico 2026</p>
</div>
""", unsafe_allow_html=True)

# --- KPIs superiores ---
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown('<div class="metric-card"><div class="metric-val">42,729</div><div class="metric-label">Electores Registrados</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown('<div class="metric-card"><div class="metric-val" style="color:#22c55e">38%</div><div class="metric-label">Aprobación Actual</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown('<div class="metric-card"><div class="metric-val" style="color:#ef4444">27</div><div class="metric-label">Incidencias Activas</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown('<div class="metric-card"><div class="metric-val" style="color:#38bdf8">71%</div><div class="metric-label">Satisfacción Lonchecito</div></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#a78bfa">{datetime.now().strftime("%H:%M")}</div><div class="metric-label">Última Actualización</div></div>', unsafe_allow_html=True)

st.divider()

# =============================================================================
# 7. LAYOUT EN DOS COLUMNAS PRINCIPALES
# =============================================================================

col_mapa, col_panel = st.columns([1.4, 1], gap="large")

# -----------------------------------------------------------------------
# COLUMNA IZQUIERDA: MAPA DE CALOR GEOGRÁFICO
# -----------------------------------------------------------------------
with col_mapa:
    st.subheader("🗺️ Mapa de Calor — Incidencias por Sector")

    # Selector de capa
    capa = st.radio(
        "Visualizar:",
        ["🔴 Incidencias", "✅ Estado por Sector", "👥 Densidad Electoral"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if "Incidencias" in capa:
        fig_mapa = px.scatter_mapbox(
            SECTORES,
            lat="lat", lon="lon",
            size="incidencias",
            color="estado",
            color_discrete_map=COLOR_MAP,
            hover_name="sector",
            hover_data={"descripcion": True, "incidencias": True, "lat": False, "lon": False},
            size_max=35,
            zoom=14.5,
            center={"lat": -12.0435, "lon": -77.0965},
            mapbox_style="carto-darkmatter",
            title="",
            height=480,
        )
    elif "Estado" in capa:
        fig_mapa = px.scatter_mapbox(
            SECTORES,
            lat="lat", lon="lon",
            color="estado",
            color_discrete_map=COLOR_MAP,
            hover_name="sector",
            hover_data={"descripcion": True},
            size_max=20,
            zoom=14.5,
            center={"lat": -12.0435, "lon": -77.0965},
            mapbox_style="carto-darkmatter",
            height=480,
        )
    else:
        # Densidad electoral simulada
        df_densidad = SECTORES.copy()
        df_densidad["electores_est"] = [1800, 2100, 900, 2400, 1600, 1200, 1900, 1400, 800, 1700]
        fig_mapa = px.scatter_mapbox(
            df_densidad,
            lat="lat", lon="lon",
            size="electores_est",
            color="electores_est",
            color_continuous_scale="Oranges",
            hover_name="sector",
            size_max=40,
            zoom=14.5,
            center={"lat": -12.0435, "lon": -77.0965},
            mapbox_style="carto-darkmatter",
            height=480,
        )

    fig_mapa.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(10,18,34,0.85)", font=dict(color="white")),
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

    # Tabla resumen compacta
    st.caption("📋 Detalle de sectores")
    df_display = SECTORES[["sector", "estado", "incidencias", "descripcion"]].copy()
    df_display.columns = ["Sector", "Estado", "Incid.", "Descripción"]

    def color_estado(val):
        colors = {"Crítico": "color: #ef4444", "Riesgo": "color: #eab308", "Estable": "color: #22c55e"}
        return colors.get(val, "")

    st.dataframe(
        df_display.style.applymap(color_estado, subset=["Estado"]),
        use_container_width=True,
        hide_index=True,
        height=200,
    )

# -----------------------------------------------------------------------
# COLUMNA DERECHA: MONITOR DE INCIDENCIAS + AGENTE IA
# -----------------------------------------------------------------------
with col_panel:

    # --- TABS del panel derecho ---
    tab_ia, tab_sentimiento, tab_incidencias = st.tabs([
        "🤖 Agente IA", "📊 Sentimiento", "🚨 Incidencias"
    ])

    # ===== TAB 1: AGENTE COPYWRITER =====
    with tab_ia:
        st.markdown("#### ✍️ Copywriter Político — Director de Comunicaciones")
        st.caption("El agente responde con tono chalaco, resaltando programas reales de gestión.")

        # Seleccionar sector de contexto
        sector_contexto = st.selectbox(
            "Sector del vecino:",
            options=["Sin especificar"] + list(SECTORES["sector"]),
        )

        comentario = st.text_area(
            "💬 Comentario del vecino:",
            placeholder='Ej: "Alcalde, la calle Puno está llena de basura y nadie viene a recogerla..."',
            height=110,
        )

        # Ejemplos rápidos
        with st.expander("💡 Comentarios de ejemplo"):
            ejemplos = [
                "Mi hijo no tiene trabajo y los programas municipales no llegan a mi zona.",
                "El Lonchecito llegó tarde esta semana y los niños se quedaron sin lonche.",
                "Hay pandillaje en Jr. Independencia y el serenazgo no aparece de noche.",
                "¿Cuándo van a arreglar el bache de Av. 1° de Mayo? Ya es el tercer mes.",
            ]
            for ej in ejemplos:
                if st.button(f"📌 {ej[:55]}...", key=ej[:20], use_container_width=True):
                    st.session_state["comentario_cargado"] = ej

        # Cargar ejemplo si fue seleccionado
        if "comentario_cargado" in st.session_state:
            comentario = st.session_state["comentario_cargado"]

        boton = st.button(
            "🚀 Generar Respuesta Estratégica",
            type="primary",
            use_container_width=True,
            disabled=not GEMINI_OK,
        )

        if boton:
            if not comentario.strip():
                st.warning("⚠️ Escribe o selecciona un comentario de vecino primero.")
            else:
                with st.spinner("🤖 El Director de Comunicaciones está redactando..."):
                    ctx = sector_contexto if sector_contexto != "Sin especificar" else ""
                    respuesta = generar_respuesta_politica(comentario, ctx)
                    time.sleep(0.5)

                st.success("✅ Respuesta generada")
                st.markdown("---")
                st.markdown("**📣 Respuesta lista para publicar:**")
                st.text_area("", value=respuesta, height=220, label_visibility="collapsed")

                col_copy1, col_copy2 = st.columns(2)
                with col_copy1:
                    st.download_button(
                        "⬇️ Descargar .txt",
                        data=respuesta,
                        file_name=f"respuesta_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with col_copy2:
                    st.info("📋 Selecciona el texto para copiar")

    # ===== TAB 2: ANÁLISIS DE SENTIMIENTO =====
    with tab_sentimiento:
        st.markdown("#### 📊 Análisis de Sentimiento Electoral")
        st.caption("Estimación de presencia digital y territorial — Actualización semanal")

        # Aprobación propia
        st.markdown("**🏛️ Indicadores de Gestión**")
        for label, val in SENTIMIENTO_GLOBAL.items():
            color = "#22c55e" if val >= 50 else "#f97316" if val >= 35 else "#ef4444"
            st.markdown(f"<span style='font-size:.8rem;color:#94a3b8'>{label}</span>", unsafe_allow_html=True)
            st.progress(val / 100, text=f"{val}%")

        st.divider()

        # Oposición
        st.markdown("**⚔️ Presencia de Oposición**")
        for candidato, data in OPOSICION.items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(
                    f"<span style='font-size:.8rem;color:{data['color']}'>{candidato}</span>",
                    unsafe_allow_html=True
                )
                st.progress(data["presencia"] / 100, text=f"{data['presencia']}%")
            with col_b:
                tendencia_color = "#22c55e" if "▲" in data["tendencia"] else "#ef4444"
                st.markdown(
                    f"<br><span style='color:{tendencia_color};font-size:.9rem'>{data['tendencia']}</span>",
                    unsafe_allow_html=True
                )

        # Alerta estratégica
        st.divider()
        st.markdown("**🚨 Alerta Estratégica**")
        if OPOSICION["Daniel Lecca (Ren. Popular)"]["presencia"] > 25:
            st.error("⚠️ Daniel Lecca supera umbral de riesgo (25%). Reforzar presencia en Zona Alta.")
        if OPOSICION["Edith Quezada"]["presencia"] > 30:
            st.warning("📌 Edith Quezada activa en redes. Contrarrestar con contenido de Lonchecito.")

    # ===== TAB 3: INCIDENCIAS =====
    with tab_incidencias:
        st.markdown("#### 🚨 Monitor de Incidencias en Tiempo Real")

        filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "Crítico", "Riesgo", "Estable"])
        df_filtrado = SECTORES if filtro_estado == "Todos" else SECTORES[SECTORES["estado"] == filtro_estado]

        for _, row in df_filtrado.iterrows():
            clase = row["estado"].lower()
            icon = "🔴" if clase == "crítico" else "🟡" if clase == "riesgo" else "🟢"
            st.markdown(f"""
<div class="incident-box {'estable' if clase=='estable' else 'riesgo' if clase=='riesgo' else ''}">
    {icon} <strong>{row['sector']}</strong><br>
    <small style="color:#94a3b8">{row['descripcion']}</small><br>
    <small style="color:#475569">Incidencias: {row['incidencias']} | Estado: {row['estado']}</small>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 8. SIDEBAR — CONTROLES Y CONFIGURACIÓN
# =============================================================================

with st.sidebar:
    st.markdown("### 🏛️ Panel de Control")
    st.caption("Sistema de Mando Único · v1.0")
    st.divider()

    st.markdown("**⚙️ Estado del Sistema**")
    if GEMINI_OK:
        st.success("✅ Gemini API activo")
    else:
        st.error("❌ Gemini API no configurado")

    st.divider()
    st.markdown("**📅 Elecciones 2026**")
    eleccion = datetime(2026, 10, 4)
    dias_restantes = (eleccion - datetime.now()).days
    st.metric("Días para el 4 Oct 2026", f"{dias_restantes} días")

    st.divider()
    st.markdown("**🗺️ Referencias del Distrito**")
    st.caption("""
    - Alcalde: Edwards J. Infante López
    - Período: 2023 – 2026  
    - Partido: Contigo Callao
    - Electores: 42,729
    - Superficie: 2.12 km²
    - Provincia: Callao
    """)

    st.divider()
    if st.button("🔄 Actualizar Dashboard", use_container_width=True):
        st.rerun()
