import streamlit as st
import pandas as pd
import os
import unicodedata
import base64
import io

def img_to_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

st.set_page_config(
    page_title="Deuda Externa Pública 2020-2025(junio)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== MOVER LOGO HACIA ARRIBA =====
st.markdown("""
    <style>
        .logo-arriba {
            margin-top: -40px;
        }
        /* Alinear números a la derecha en st.dataframe */
        [data-testid="stDataFrame"] td {
            text-align: right !important;
            font-family: monospace !important;
        }
    </style>
""", unsafe_allow_html=True)

ruta_logo = r"C:\Users\mverdezoto\Downloads\Ejer_Pub_py\assets\Escudo_BCE.png"
logo_b64 = img_to_base64(ruta_logo)


col1, col2 = st.columns([8, 1])

with col1:
    st.title("Deuda Externa Pública (2020-2025)")
    st.markdown("---")

with col2:
    st.markdown(f"""
        <img src="data:image/png;base64,{logo_b64}" 
             class="logo-arriba" 
             style="width:100%;">
    """, unsafe_allow_html=True)



# ======================================================
# CARGA DE DATOS
# ======================================================

@st.cache_data
def cargar_datos():
    archivo = "Base Plana 20-25.xlsx"

    if not os.path.exists(archivo):
        st.error("No se encuentra 'Base Plana 20-25.xlsx'")
        st.stop()

    df = pd.read_excel(archivo, engine="openpyxl")

    # Normalizar columnas
    cols = []
    for c in df.columns:
        limpio = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
        limpio = (
            limpio.replace("\n", " ")
                  .replace("\r", " ")
                  .replace("  ", " ")
                  .strip()
                  .upper()
        )
        cols.append(limpio)

    df.columns = cols
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df


df = cargar_datos()


# ======================================================
# ORDEN MESES
# ======================================================

MESES_ORDEN = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

if "MES" in df.columns:
    df["MES"] = df["MES"].astype(str).str.upper().str.strip()


# ======================================================
# FILTROS SIDEBAR
# ======================================================

st.sidebar.header("Filtros")

def selectbox_col(nombre, columna):
    if columna not in df.columns:
        st.sidebar.caption(f"{nombre}: No encontrado")
        return "Todos"

    valores = df[columna].dropna().astype(str).str.strip().unique().tolist()

    if columna == "MES":
        valores = sorted([v for v in valores if v in MESES_ORDEN], key=lambda x: MESES_ORDEN[x])
    else:
        valores = sorted(valores)

    return st.sidebar.selectbox(nombre, ["Todos"] + valores)


periodo   = selectbox_col("Periodo", "PERIODO")
trimestre = selectbox_col("Trimestre", "TRIMESTRE")
mes       = selectbox_col("Mes", "MES")
tipo_acre = selectbox_col("Tipo de Acreedor", "TIPO DE ACREEDOR")
acreedor  = selectbox_col("Nombre del Acreedor", "NOMBRE DEL ACREEDOR")
deudor    = selectbox_col("Deudor", "DEUDOR") 
no_prestamos = selectbox_col("No. Préstamos", "N_PRESTAMOS")


# ======================================================
# APLICAR FILTROS
# ======================================================
df_f = df.copy()

if periodo != "Todos":
    df_f = df_f[df_f["PERIODO"].astype(str) == str(periodo)]

if trimestre != "Todos":
    df_f = df_f[df_f["TRIMESTRE"].astype(str) == str(trimestre)]

if mes != "Todos":
    df_f = df_f[df_f["MES"] == mes]

if tipo_acre != "Todos":
    df_f = df_f[df_f["TIPO DE ACREEDOR"] == tipo_acre]

if acreedor != "Todos":
    df_f = df_f[df_f["NOMBRE DEL ACREEDOR"] == acreedor]

if deudor != "Todos":
    df_f = df_f[df_f["DEUDOR"] == deudor]
    
if no_prestamos != "Todos":
    df_f = df_f[df_f["N_PRESTAMOS"].astype(str) == str(no_prestamos)]

if df_f.empty:
    st.warning("No hay datos con esos filtros.")
    st.stop()


# ======================================================
# COLUMNAS FINANCIERAS
# ======================================================

claves = [
    "SALDO INICIAL","DESEMBOLSOS","PRINCIPAL REEMBOLSADO",
    "PRINCIPAL CANJEADO","PRINCIPAL CONDONADO","INTERESES PAGADOS",
    "INTERESES CONDONADOS","INTERESES POR MORA","INTERESES CANJEADOS",
    "COMISIONES PAGADAS","COMISIONES CONDONADAS","AJUSTE","SALDO FINAL",
    "ATRASOS CAP","ATRASOS INT","SALDO+ATR"
]

cols_fin = [c for c in df.columns if any(k in c for k in claves)]

# Convertir columnas financieras a número
df_f[cols_fin] = df_f[cols_fin].apply(pd.to_numeric, errors="coerce")


# ======================================================
# FORMATEO USD + ALINEACIÓN
# ======================================================

df_formateado = df_f.copy()

for c in cols_fin:
    df_formateado[c] = df_formateado[c].apply(
        lambda x: f"{x:,.2f}" if pd.notnull(x) else ""
    )


# ======================================================
# TABLA RESULTADOS
# ======================================================

st.subheader(f"Registros encontrados: {len(df_f):,} filas")

columnas_info = [
    "PERIODO","TRIMESTRE","MES",
    "TIPO DE ACREEDOR","NOMBRE DEL ACREEDOR",
    "DEUDOR","N_PRESTAMOS"
]

columnas_finales = [c for c in columnas_info if c in df_f.columns] + cols_fin

st.dataframe(df_formateado[columnas_finales], use_container_width=True, hide_index=True)


# ======================================================
# TOTALES
# ======================================================

st.markdown("---")
st.subheader("Total General")

totales = df_f[cols_fin].sum()
totales_df = pd.DataFrame([totales.apply(lambda x: f"{x:,.2f}")])

st.dataframe(totales_df, use_container_width=True, hide_index=True)


# ======================================================
# DESCARGA
# ======================================================

output = io.BytesIO()

# Crear archivo Excel en memoria
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_f[columnas_finales].to_excel(writer, index=False, sheet_name="Deuda_Filtrada")

excel_data = output.getvalue()

st.download_button(
    label="Descargar Reporte en Excel",
    data=excel_data,
    file_name="deuda_filtrada.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.success("Cargado correctamente")
