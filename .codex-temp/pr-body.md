## Qué cambia

- Añade `dashboard/streamlit_app.py` como punto de entrada para Streamlit Community Cloud.
- Carga el dashboard HTML autocontenido en un iframe aislado compatible con JavaScript.
- Fija Streamlit 1.60.0 y excluye artefactos locales de Python.

## Motivo

El dashboard existente estaba preparado como sitio HTML, pero Streamlit Community Cloud necesita un archivo Python de entrada y una declaración de dependencias.

## Impacto

Permite desplegar el dashboard desde la rama de GitHub usando `dashboard/streamlit_app.py`, sin modificar sus gráficas o datos.

## Validación

- `streamlit.testing.v1.AppTest`: correcto
- Compilación de Python: correcta
- Endpoint local `/_stcore/health`: HTTP 200
