import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="DSS | L'KAFICE",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #101C2C;
        color: #F8FAFC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        background-color: #17263A;
        border-right: 1px solid #344357;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC;
    }

    [data-testid="stMetric"] {
        background-color: #1C2B40;
        border: 1px solid #344357;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    [data-testid="stMetricLabel"] {
        color: #D0D9E5 !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    h1, h2, h3 {
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }

    hr {
        border-color: #344357;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent

@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return None
    # Try common encodings to avoid CSV import problems.
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)

kpi = load_csv("kpi_dss.csv")
diagnostico = load_csv("diagnostico_dss.csv")
plan = load_csv("plan_accion_dss.csv")

st.sidebar.title("☕ L'KAFICE")
st.sidebar.caption("Sistema de apoyo a la toma de decisiones")
page = st.sidebar.radio(
    "NAVEGACIÓN",
    ["Resumen ejecutivo", "Diagnóstico operativo", "Plan de acción", "Explorar datos"],
)
st.sidebar.divider()
st.sidebar.caption("Proyecto académico · Datos sintéticos")

st.title("Sistema de Apoyo a la Toma de Decisiones")
st.markdown("**L'KAFICE | Gestión y mejora de operaciones**")
st.caption("Panel académico basado en datos sintéticos. Las metas son ilustrativas y deben validarse con la empresa.")

if kpi is None or diagnostico is None or plan is None:
    st.error("Faltan uno o más archivos CSV. Coloca los tres CSV junto a app.py: kpi_dss.csv, diagnostico_dss.csv y plan_accion_dss.csv.")
    st.stop()

# Normalizar textos para facilitar la búsqueda de columnas.
kpi.columns = [str(c).strip() for c in kpi.columns]
diagnostico.columns = [str(c).strip() for c in diagnostico.columns]
plan.columns = [str(c).strip() for c in plan.columns]

def find_col(df, candidates):
    for candidate in candidates:
        for col in df.columns:
            if col.casefold() == candidate.casefold():
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
    try:
        number = float(str(value).replace("%", "").replace(",", "."))
        # Results exported as percentages may be either 15.2 or 0.152.
        formatted = f"{number:.2f}"
        if "%" in unit or "porcentaje" in unit.casefold():
            formatted += "%"
        elif unit and unit.casefold() not in ("nan", "none"):
            formatted += f" {unit}"
    except (TypeError, ValueError):
        formatted = str(value)
    st.metric(title, formatted)

if page == "Resumen ejecutivo":
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
        st.markdown("#### Indicadores registrados")
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
            if not chart_df.empty:
                fig = px.bar(chart_df, x="Indicador", y="Resultado numérico", text="Resultado",
                             color="Indicador", title="Resultados de los KPI")
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#101C2C",
                    plot_bgcolor="#101C2C",
                    font=dict(color="#F8FAFC"),
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="Resultado",
                    margin=dict(l=10, r=10, t=55, b=10),
                )
                fig.update_xaxes(showgrid=False, tickfont=dict(color="#D0D9E5"))
                fig.update_yaxes(gridcolor="#344357", zerolinecolor="#344357")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(kpi, use_container_width=True, hide_index=True)
        else:
            st.dataframe(kpi, use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### Estado del diagnóstico")
        state_col = find_col(diagnostico, ["Estado"])
        if state_col:
            counts = diagnostico[state_col].fillna("Sin estado").astype(str).value_counts().reset_index()
            counts.columns = ["Estado", "Cantidad"] 
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#101C2C",
                plot_bgcolor="#101C2C",
                font=dict(color="#F8FAFC"),
                margin=dict(l=10, r=10, t=55, b=10),
                legend_title="",
                legend=dict(font=dict(color="#F8FAFC")),
            )
            fig.update_traces(textfont=dict(color="#FFFFFF"))
(counts, names="Estado", values="Cantidad", hole=0.55, title="Indicadores por estado")
            fig.update_layout(margin=dict(l=10,r=10,t=55,b=10), legend_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontró la columna 'Estado' en el archivo de diagnóstico.")
    st.info("Interpretación: usa estos resultados para priorizar mejoras. Las metas del diagnóstico son supuestos académicos hasta que L'KAFICE las confirme.")

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
    st.dataframe(view, use_container_width=True, hide_index=True)
    if state_col:
        st.markdown("### Resumen de cumplimiento")

    if view.empty:
        st.info("No hay indicadores para los filtros seleccionados.")
    else:
        counts = view[state_col].fillna("Sin estado").astype(str).value_counts().reset_index()
        counts.columns = ["Estado", "Cantidad"]

        fig = px.bar(
            counts,
            x="Estado",
            y="Cantidad",
            text="Cantidad",
            color="Estado"
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Número de indicadores"
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "Plan de acción":
    st.subheader("Plan de acción")
    st.write("Acciones propuestas para mejorar los resultados operativos.")
    priority_col = find_col(plan, ["Prioridad"])
    if priority_col:
        opts = ["Todas"] + sorted(plan[priority_col].dropna().astype(str).unique().tolist())
        selected = st.selectbox("Filtrar por prioridad", opts)
        if selected != "Todas":
            plan_view = plan[plan[priority_col].astype(str) == selected]
        else:
            plan_view = plan
    else:
        plan_view = plan
    st.dataframe(plan_view, use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar plan de acción (CSV)",
        data=plan_view.to_csv(index=False).encode("utf-8-sig"),
        file_name="plan_accion_filtrado.csv",
        mime="text/csv",
    )

else:
    st.subheader("Explorar datos")
    data_choice = st.selectbox("Selecciona una tabla", ["KPI", "Diagnóstico", "Plan de acción"])
    data_map = {"KPI": kpi, "Diagnóstico": diagnostico, "Plan de acción": plan}
    selected_df = data_map[data_choice]
    st.caption(f"{len(selected_df)} filas · {len(selected_df.columns)} columnas")
    search = st.text_input("Buscar texto en la tabla")
    if search:
        mask = selected_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        selected_df = selected_df[mask]
    st.dataframe(selected_df, use_container_width=True, hide_index=True)
    st.download_button(
        f"Descargar {data_choice.lower()} (CSV)",
        data=selected_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{data_choice.lower().replace(' ', '_')}_dss.csv",
        mime="text/csv",
    )

st.divider()
st.caption("DSS L'KAFICE · Herramienta académica de apoyo a la decisión · Validar resultados y metas antes de uso empresarial.")
