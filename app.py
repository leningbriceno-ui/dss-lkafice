import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from auditoria_as_is import auditar, DatosIncompatibles

st.set_page_config(
    page_title="DSS | Empresa A",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #101C2C; color: #F8FAFC; }
    .block-container { padding-top: 2rem; padding-bottom: 2.5rem; max-width: 1500px; }
    [data-testid="stSidebar"] { background-color: #17263A; border-right: 1px solid #344357; }
    [data-testid="stSidebar"] * { color: #F8FAFC; }
    [data-testid="stMetric"] {
        background-color: #1C2B40; border: 1px solid #344357; padding: 20px;
        border-radius: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); min-height: 112px;
    }
    [data-testid="stMetricLabel"] { color: #D0D9E5 !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700; font-size: clamp(1.35rem, 2vw, 2.15rem); }
    h1, h2, h3, h4 { color: #FFFFFF; letter-spacing: -0.02em; }
    hr { border-color: #344357; }
    div[data-testid="stAlert"] { border-radius: 12px; }
    div[data-testid="stDataFrame"] { border: 1px solid #344357; border-radius: 10px; overflow: hidden; }
    div.stDownloadButton > button { border: 1px solid #D9B568; border-radius: 10px; }
/* Igualar la barra superior con el fondo de la aplicación */
.stAppHeader,
header[data-testid="stHeader"] {
    background-color: #101C2C !important;
    background: #101C2C !important;
    border-bottom: none !important;
}

/* Mantener la barra de herramientas integrada al diseño */
[data-testid="stToolbar"] {
    background-color: #101C2C !important;
}

/* Evitar que aparezca una franja blanca al desplazarse */
.stApp {
    background-color: #101C2C !important;
}

/* Mejorar contraste del botón de descarga CSV */
div[data-testid="stDownloadButton"] button {
    background-color: #D9B568 !important;
    color: #101C2C !important;
    border: 1px solid #D9B568 !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}

div[data-testid="stDownloadButton"] button p {
    color: #101C2C !important;
    font-weight: 700 !important;
}

div[data-testid="stDownloadButton"] button:hover {
    background-color: #C6A04E !important;
    border-color: #C6A04E !important;
}

/* Mejorar contraste de etiquetas de filtros y campos de búsqueda */
div[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] label,
label[data-testid="stWidgetLabel"],
.stSelectbox label,
.stTextInput label,
.stMultiSelect label,
.stRadio label,
.stNumberInput label,
.stDateInput label,
.stSlider label {
    color: #D0D9E5 !important;
    opacity: 1 !important;
}

/* Mantener legibles los textos auxiliares de los controles */
div[data-testid="stWidgetLabel"] small {
    color: #B8C5D6 !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent

@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)

kpi = load_csv("kpi_dss.csv")
diagnostico = load_csv("diagnostico_dss.csv")
plan = load_csv("plan_accion_dss.csv")
ARCHIVO_REALES = DATA_DIR / "ventas_reales_octubre_2026.csv"

st.sidebar.title("☕ Empresa A")
st.sidebar.caption("Sistema de apoyo a la toma de decisiones")
page = st.sidebar.radio(
    "NAVEGACIÓN",
    ["Resumen ejecutivo", "Diagnóstico operativo", "Plan de acción", "Explorar datos"],
)
st.sidebar.divider()
modo = st.sidebar.radio(
    "ORIGEN DE DATOS",
    ["Sintéticos: demostración técnica", "Reales: auditoría AS-IS (uso privado)"],
)
modo_real = modo.startswith("Reales")
st.sidebar.caption("Datos reales y sintéticos siempre separados")

st.title("Sistema de Apoyo a la Toma de Decisiones")
st.markdown("**Empresa A | Gestión y mejora de operaciones**")
if modo_real:
    st.caption("Empresa A · Octubre de 2026 · Datos reales agregados de comprobantes. No equivalen a pedidos.")
else:
    st.caption("Demostración con datos sintéticos. Las metas son ilustrativas y NO son resultados de la empresa.")

if not modo_real and (kpi is None or diagnostico is None or plan is None):
    st.error("Faltan uno o más archivos CSV. Coloca los tres archivos junto a app.py: kpi_dss.csv, diagnostico_dss.csv y plan_accion_dss.csv.")
    st.stop()

for tabla in (kpi, diagnostico, plan):
    if tabla is not None:
        tabla.columns = [str(c).strip() for c in tabla.columns]


def find_col(df, candidates):
    for candidate in candidates:
        for col in df.columns:
            if str(col).casefold() == candidate.casefold():
                return col
    return None


def metric_value(label_candidates):
    col_label = find_col(kpi, ["Indicador"])
    col_value = find_col(kpi, ["Resultado", "Valor"])
    if col_label is None or col_value is None:
        return None
    labels = kpi[col_label].astype(str).str.casefold()
    for candidate in label_candidates:
        mask = labels.str.contains(candidate.casefold(), regex=False, na=False)
        if mask.any():
            value = kpi.loc[mask, col_value].iloc[0]
            unit_col = find_col(kpi, ["Unidad"])
            unit = str(kpi.loc[mask, unit_col].iloc[0]) if unit_col else ""
            return value, unit
    return None


def display_metric(title, candidates, fallback="—"):
    result = metric_value(candidates)
    if result is None:
        st.metric(title, fallback)
        return
    value, unit = result
    is_productivity = "productividad" in title.casefold()
    try:
        number = float(str(value).replace("%", "").replace(",", "."))
        if is_productivity:
            formatted = f"{number:.2f} pedidos"
        elif "%" in unit or "porcentaje" in unit.casefold():
            formatted = f"{number:.2f}%"
        elif unit and unit.casefold() not in ("nan", "none"):
            formatted = f"{number:.2f} {unit}"
        else:
            formatted = f"{number:.2f}"
    except (TypeError, ValueError):
        formatted = str(value)
    st.metric(title, formatted)
    if is_productivity:
        st.caption("Por trabajador/día")


def apply_dark_chart_style(fig, show_legend=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#101C2C",
        plot_bgcolor="#101C2C",
        font=dict(color="#F8FAFC"),
        title_font=dict(color="#F8FAFC", size=18),
        showlegend=show_legend,
        margin=dict(l=12, r=12, t=55, b=12),
        legend=dict(font=dict(color="#F8FAFC")),
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(color="#D0D9E5"), automargin=True)
    fig.update_yaxes(gridcolor="#344357", zerolinecolor="#344357", tickfont=dict(color="#D0D9E5"), automargin=True)
    return fig


def renderizar_real(pagina):
    try:
        resumen, registros = auditar(ARCHIVO_REALES)
    except DatosIncompatibles as exc:
        st.error(f"Datos reales no disponibles o inconsistentes: {exc}")
        st.stop()

    df = pd.DataFrame(registros)
    dias = df.loc[~df["es_sabado"]].copy()
    st.info("FUENTE REAL: comprobantes agregados de octubre. La productividad en **pedidos/trabajador/día** sigue pendiente de un registro de pedidos completados.")

    if pagina == "Resumen ejecutivo":
        st.subheader("Resumen ejecutivo · registros reales AS-IS")
        a,b,c = st.columns(3)
        with a:
            st.metric("Comprobantes (mes completo)", f'{resumen["comprobantes_total"]:,}')
        with b:
            st.metric("Comprobantes lunes–viernes", f'{resumen["comprobantes_lun_vie"]:,}')
        with c:
            st.metric("Ventas monetarias", f'S/ {resumen["venta_total_soles"]:,.2f}')
        a,b,c=st.columns(3)
        with a:
            st.metric("Días laborables observados", resumen["dias_lun_vie"])
        with b:
            st.metric("Trabajador-días (lunes–viernes)", resumen["trabajador_dias_lun_vie"])
        with c:
            st.metric("Comprobantes/trabajador/día", f'{resumen["comprobantes_por_trabajador_dia"]:.2f}')
        st.caption("Este resultado es un indicador auxiliar de comprobantes, NO productividad por pedidos. Los sábados se presentan aparte porque no se dispone de su dotación.")
        fig=px.bar(dias,x="fecha",y="comprobantes_activos",title="Comprobantes diarios (lunes a viernes)",labels={"fecha":"Fecha","comprobantes_activos":"Comprobantes"})
        apply_dark_chart_style(fig, show_legend=False)
        st.plotly_chart(fig,use_container_width=True)
        st.write(f'Sábados: {resumen["comprobantes_sabados"]} comprobantes en {resumen["sabados_con_ventas"]} fechas, excluidos de la tasa por trabajador.')
    elif pagina == "Diagnóstico operativo":
        st.subheader("Diagnóstico de actividad · datos reales")
        st.write("El análisis describe comprobantes y ventas; no mide aún tiempos de atención, errores o pedidos completados.")
        st.dataframe(pd.DataFrame([
            {"Comprobación":"Cuadre de canales", "Resultado":"Superado: cada día coincide"},
            {"Comprobación":"Cobertura", "Resultado":f'{resumen["dias_lun_vie"]} días laborables + {resumen["sabados_con_ventas"]} sábados'},
            {"Comprobación":"Dotación laborable", "Resultado":f'{resumen["trabajador_dias_lun_vie"]} trabajador-días confirmados'},
            {"Comprobación":"Pedidos completados", "Resultado":"No disponibles por día; KPI principal pendiente"},
        ]),use_container_width=True,hide_index=True)
        fig=px.line(dias,x="fecha",y="comprobantes_activos",markers=True,title="Variabilidad diaria de comprobantes")
        apply_dark_chart_style(fig,show_legend=False)
        st.plotly_chart(fig,use_container_width=True)
    elif pagina == "Plan de acción":
        st.subheader("Acciones de validación propuestas · sin implementación confirmada")
        st.dataframe(pd.DataFrame([
            {"Prioridad":"Alta", "Actividad":"Conseguir exportación o conteo diario de pedidos completados", "Propósito":"Calcular productividad principal"},
            {"Prioridad":"Alta", "Actividad":"Reconciliar los comprobantes del informe con los pedidos mostrados por el panel", "Propósito":"Determinar unidad y alcance de cada indicador"},
            {"Prioridad":"Media", "Actividad":"Registrar tiempos, errores y demoras por pedido en observación", "Propósito":"Analizar causas con BPM–Lean"},
            {"Prioridad":"Media", "Actividad":"Documentar y probar la propuesta sin atribuir mejoras observadas", "Propósito":"Delimitar la validación técnica y trabajo futuro"},
        ]),use_container_width=True,hide_index=True)
        st.warning("No se han ejecutado ni demostrado mejoras del proceso. Este plan no presenta metas sintéticas como logros reales.")
    elif pagina == "Explorar datos":
        st.subheader("Explorar registros agregados de ventas reales")
        filtro=st.selectbox("Periodo",["Todas las fechas","Solo lunes a viernes","Solo sábados"])
        vista=df.copy()
        if filtro=="Solo lunes a viernes":
            vista=vista[~vista["es_sabado"]]
        elif filtro=="Solo sábados":
            vista=vista[vista["es_sabado"]]
        vista=vista.drop(columns=["es_sabado"])
        st.caption(f"{len(vista)} fechas · Fuente: informe original de ventas, agregado y anonimizado")
        st.dataframe(vista,use_container_width=True,hide_index=True)
        st.download_button("Descargar agregados (CSV)",data=vista.to_csv(index=False).encode("utf-8-sig"),file_name="ventas_reales_agregadas.csv",mime="text/csv")


if modo_real:
    if not ARCHIVO_REALES.exists():
        st.warning("Los registros reales no se publican en este repositorio por confidencialidad.")
        st.info("Para ejecutar la auditoría AS-IS, utiliza un entorno local o privado y coloca "
                "el archivo ventas_reales_octubre_2026.csv junto a app.py. "
                "La demostración pública funciona con datos sintéticos.")
        st.stop()
    renderizar_real(page)
elif page == "Resumen ejecutivo":
    st.subheader("Resumen ejecutivo")
    st.write("Vista rápida de los indicadores clave para identificar oportunidades de mejora.")

    c1, c2, c3 = st.columns(3)
    with c1:
        display_metric("Tiempo promedio de atención", ["tiempo promedio", "tiempo de atención"])
    with c2:
        display_metric("Pedidos demorados", ["demorados", "demora"])
    with c3:
        display_metric("Pedidos con errores", ["pedidos con error", "pedido con error", "errores"])

    c4, c5, c6 = st.columns(3)
    with c4:
        display_metric("Cumplimiento correcto", ["cumplimiento correcto", "pedido correcto"])
    with c5:
        display_metric("Desperdicio operativo", ["desperdicio"])
    with c6:
        display_metric("Productividad diaria", ["productividad"])

    st.divider()
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Indicadores porcentuales")
        label_col = find_col(kpi, ["Indicador"])
        value_col = find_col(kpi, ["Resultado", "Valor"])
        if label_col and value_col:
            chart_df = kpi[[label_col, value_col]].copy()
            chart_df.columns = ["Indicador", "Resultado"]
            chart_df["Resultado numérico"] = pd.to_numeric(
                chart_df["Resultado"].astype(str).str.replace("%", "", regex=False).str.replace(",", ".", regex=False),
                errors="coerce",
            )
            chart_df = chart_df.dropna(subset=["Resultado numérico"])
            unidad_col = find_col(kpi, ["Unidad"])
            if unidad_col:
                porcentajes = kpi[[label_col, unidad_col]].copy()
                porcentajes.columns = ["Indicador", "Unidad"]
                chart_df = chart_df.merge(porcentajes, on="Indicador", how="left")
                chart_df = chart_df[
                    chart_df["Unidad"].astype(str).str.contains("%|porcentaje", case=False, regex=True, na=False)
                ].copy()
            if not chart_df.empty:
                fig = px.bar(
                    chart_df, x="Indicador", y="Resultado numérico", text="Resultado",
                    title="Indicadores porcentuales (datos sintéticos)", color_discrete_sequence=["#D9B568"],
                )
                apply_dark_chart_style(fig, show_legend=False)
                fig.update_traces(textposition="outside", cliponaxis=False, textfont=dict(color="#F8FAFC"))
                fig.update_layout(xaxis_title="", yaxis_title="Porcentaje (%)", xaxis_tickangle=-25)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(kpi, use_container_width=True, hide_index=True)
        else:
            st.dataframe(kpi, use_container_width=True, hide_index=True)

    with right:
        st.markdown("#### Estado del diagnóstico")
        state_col = find_col(diagnostico, ["Estado"])
        if state_col:
            counts = (
                diagnostico[state_col].fillna("Sin estado").astype(str)
                .value_counts().rename_axis("Estado").reset_index(name="Cantidad")
            )
            fig = px.pie(
                counts, names="Estado", values="Cantidad", hole=0.55,
                title="Indicadores por estado", color="Estado",
                color_discrete_map={"CUMPLE": "#2CB67D", "NO CUMPLE": "#F08A78", "Sin estado": "#D9B568"},
                color_discrete_sequence=["#D9B568", "#F08A78", "#6CB6FF"],
            )
            apply_dark_chart_style(fig, show_legend=True)
            fig.update_traces(textfont=dict(color="#FFFFFF"), textposition="inside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontró la columna 'Estado' en el archivo de diagnóstico.")

    st.info("Interpretación: usa estos resultados para priorizar mejoras. Las metas del diagnóstico son supuestos académicos hasta que Empresa A las confirme.")

elif page == "Diagnóstico operativo":
    st.subheader("Diagnóstico operativo")
    st.write("Revisa el estado de cada indicador y las acciones sugeridas.")
    state_col = find_col(diagnostico, ["Estado"])
    priority_col = find_col(diagnostico, ["Prioridad"])
    col1, col2 = st.columns(2)
    with col1:
        if state_col:
            options = ["Todos"] + sorted(diagnostico[state_col].dropna().astype(str).unique().tolist())
            selected_state = st.selectbox("Filtrar por estado", options)
        else:
            selected_state = "Todos"
    with col2:
        if priority_col:
            options_p = ["Todas"] + sorted(diagnostico[priority_col].dropna().astype(str).unique().tolist())
            selected_priority = st.selectbox("Filtrar por prioridad", options_p)
        else:
            selected_priority = "Todas"
    view = diagnostico.copy()
    if state_col and selected_state != "Todos":
        view = view[view[state_col].astype(str) == selected_state]
    if priority_col and selected_priority != "Todas":
        view = view[view[priority_col].astype(str) == selected_priority]
    if view.empty:
       st.info("No hay indicadores para los filtros seleccionados.")
    else:
        st.dataframe(view, use_container_width=True, hide_index=True)

        if state_col:
            st.markdown("### Resumen de cumplimiento")
            counts = (
                view[state_col].fillna("Sin estado").astype(str)
                .value_counts()
                .rename_axis("Estado")
                .reset_index(name="Cantidad")
            )
            fig = px.bar(
                counts,
                x="Estado",
                y="Cantidad",
                text="Cantidad",
                color="Estado",
                title="Indicadores según estado",
                color_discrete_map={
                    "CUMPLE": "#2CB67D",
                    "NO CUMPLE": "#F08A78",
                },
                color_discrete_sequence=[
                    "#D9B568", "#F08A78", "#6CB6FF"
                ],
            )
            apply_dark_chart_style(fig, show_legend=False)
            fig.update_traces(
                textposition="outside",
                cliponaxis=False,
                textfont=dict(color="#F8FAFC"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "No se encontró la columna 'Estado' "
                "en el archivo de diagnóstico."
            )

elif page == "Plan de acción":
    st.subheader("Plan de acción")
    st.write("Acciones propuestas para mejorar los resultados operativos.")
    priority_col = find_col(plan, ["Prioridad"])
    if priority_col:
        opts = ["Todas"] + sorted(plan[priority_col].dropna().astype(str).unique().tolist())
        selected_priority = st.selectbox("Filtrar por prioridad", opts)
        plan_filtered = plan.copy()
        if selected_priority != "Todas":
            plan_filtered = plan_filtered[plan_filtered[priority_col].astype(str) == selected_priority]
    else:
        plan_filtered = plan.copy()
        st.info("No se encontró la columna 'Prioridad'; se muestra el plan completo.")

    # Mantener una vista de lectura rápida y permitir consultar todas las columnas del CSV.
    summary_candidates = [
        ["Indicador"], ["Accion", "Acción"], ["Estado"],
        ["Desviacion_pct", "Desviación_pct", "Desviacion", "Desviación"],
        ["Prioridad"], ["Herramienta_Lean", "Herramienta Lean", "Herramienta_Lean"],
    ]
    summary_cols = []
    for candidates in summary_candidates:
        col = find_col(plan_filtered, candidates)
        if col and col not in summary_cols:
            summary_cols.append(col)
    if not summary_cols:
        summary_cols = list(plan_filtered.columns[:6])

    plan_view_mode = st.radio(
        "Vista del plan",
        ["Resumida (lectura rápida)", "Completa (todas las columnas)"],
        horizontal=True,
        key="plan_view_mode",
    )
    if plan_view_mode == "Resumida (lectura rápida)":
        plan_view = plan_filtered[summary_cols].copy()
        st.caption(f"Vista resumida · {len(plan_view.columns)} columnas")
        download_name = "plan_accion_resumido.csv"
    else:
        plan_view = plan_filtered.copy()
        st.caption(f"Vista completa · {len(plan_view.columns)} columnas disponibles en el CSV")
        download_name = "plan_accion_completo.csv"
        if len(plan_view.columns) <= len(summary_cols):
            st.warning(
                "El CSV actual solo contiene las columnas que aparecen en la vista resumida. "
                "Para mostrar 16 columnas, primero debes subir a GitHub el archivo "
                "plan_accion_dss.csv que tenga esas 16 columnas."
            )

    st.dataframe(plan_view, use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar plan de acción (CSV)",
        data=plan_view.to_csv(index=False).encode("utf-8-sig"),
        file_name=download_name,
        mime="text/csv",
    )

else:
    st.subheader("Explorar datos")
    data_choice = st.selectbox("Selecciona una tabla", ["KPI", "Diagnóstico", "Plan de acción"])
    data_map = {"KPI": kpi, "Diagnóstico": diagnostico, "Plan de acción": plan}
    selected_df = data_map[data_choice].copy()

    if data_choice == "Plan de acción":
        summary_candidates = [
            ["Indicador"], ["Accion", "Acción"], ["Estado"],
            ["Desviacion_pct", "Desviación_pct", "Desviacion", "Desviación"],
            ["Prioridad"], ["Herramienta_Lean", "Herramienta Lean"],
        ]
        summary_cols = []
        for candidates in summary_candidates:
            col = find_col(selected_df, candidates)
            if col and col not in summary_cols:
                summary_cols.append(col)
        if not summary_cols:
            summary_cols = list(selected_df.columns[:6])
        explore_mode = st.radio(
            "Vista del plan de acción",
            ["Resumida (lectura rápida)", "Completa (todas las columnas)"],
            horizontal=True,
            key="explore_plan_view_mode",
        )
        if explore_mode == "Resumida (lectura rápida)":
            selected_df = selected_df[summary_cols].copy()

    st.caption(f"{len(selected_df)} filas · {len(selected_df.columns)} columnas")
    search = st.text_input("Buscar texto en la tabla")
    if search:
        mask = selected_df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        selected_df = selected_df[mask]
    st.dataframe(selected_df, use_container_width=True, hide_index=True)
    st.download_button(
        f"Descargar {data_choice.lower()} (CSV)",
        data=selected_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{data_choice.lower().replace(' ', '_')}_dss.csv",
        mime="text/csv",
    )

st.divider()
st.caption("DSS Empresa A · Herramienta académica de apoyo a la decisión · Validar resultados y metas antes de uso empresarial.")
