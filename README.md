# DSS BPM–Lean — Empresa A (versión pública)

Aplicación académica en Streamlit para visualizar KPI, diagnóstico operativo y plan de acción.

## Uso
- **Sintéticos: demostración técnica** es el modo predeterminado en la versión pública.
- El modo **Reales: auditoría AS-IS (uso privado)** requiere `ventas_reales_octubre_2026.csv` y debe ejecutarse en un entorno privado. **No se distribuye aquí el archivo de ventas reales.**
- Ninguna cifra del modo sintético debe interpretarse como resultado observado en la empresa.
- El indicador **comprobantes/trabajador/día** es auxiliar y distinto del indicador principal **pedidos/trabajador/día**.
- Esta aplicación no prueba por sí sola un incremento de productividad debido a BPM–Lean.

## Archivos del repositorio
- `app.py`: cuatro vistas y selector del origen de datos.
- `auditoria_as_is.py`: validación aritmética y de integridad de comprobantes diarios (para uso privado).
- `kpi_dss.csv`, `diagnostico_dss.csv`, `plan_accion_dss.csv`: datos **sintéticos**.
- `requirements.txt`: dependencias de la aplicación.
- `.gitignore`: evita incluir algunos archivos privados mediante Git; **no reemplaza la revisión manual antes de publicar**.

## Ejecución local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Confidencialidad
No subir registros reales, entrevistas, cuestionarios SUS, datos personales ni informes internos a repositorios públicos.
Un nombre comercial puede seguir siendo visible en el **nombre del repositorio** y en su historial, incluso si el código ahora dice Empresa A.
