
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="DSS | L'KAFICE",
    page_icon="☕",
    layout="wide"
)

st.title("☕ DSS L'KAFICE")
st.subheader("Sistema de apoyo a la toma de decisiones")
st.caption("Prototipo académico con datos sintéticos")

DATA_DIR = Path(__file__).parent

st.sidebar.header("Navegación")
seccion = st.sidebar.radio(
    "Selecciona una sección",
    ["Resumen ejecutivo", "Diagnóstico operativo", "Plan de acción"]
)

if seccion == "Resumen ejecutivo":
    st.header("Resumen ejecutivo")

    archivo = DATA_DIR / "kpi_dss.csv"

    if archivo.exists():
        df = pd.read_csv(archivo)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Todavía no se encuentra kpi_dss.csv.")

elif seccion == "Diagnóstico operativo":
    st.header("Diagnóstico operativo")

    archivo = DATA_DIR / "diagnostico_dss.csv"

    if archivo.exists():
        df = pd.read_csv(archivo)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Todavía no se encuentra diagnostico_dss.csv.")

else:
    st.header("Plan de acción")

    archivo = DATA_DIR / "plan_accion_dss.csv"

    if archivo.exists():
        df = pd.read_csv(archivo)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Todavía no se encuentra plan_accion_dss.csv.")
