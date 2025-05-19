import os
import pandas as pd
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget
import plotly.express as px

# Cargar el archivo CSV desde la ruta del script
ruta_actual = os.path.dirname(os.path.abspath(__file__))
archivo_csv = os.path.join(ruta_actual, "Aforos-RedPropia.csv")
df = pd.read_csv(archivo_csv, encoding="latin1")

# Limpieza
meses = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}
df['MES'] = df['MES'].str.upper().map(meses)
cols_numericas = df.columns[4:]
for col in cols_numericas:
    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Filtros
anios = sorted(df['AÑO'].dropna().unique())
meses_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
              7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
tipos_vehiculo = ['AUTOS', 'MOTOS', 'AUTOBUS DE 2 EJES', 'AUTOBUS DE 3 EJES', 'CAMIONES DE 2 EJES']

# Interfaz
app_ui = ui.page_fluid(
    ui.tags.style(open("estilo.css").read()),

    ui.panel_title("Dashboard Aforos CAPUFE", "center"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_select("anio", "Selecciona el año:", {str(a): str(a) for a in anios}),
            ui.input_select("mes", "Selecciona el mes:", {str(k): v for k, v in meses_dict.items()}),
            ui.input_select("vehiculo", "Tipo de vehículo:", {v: v for v in tipos_vehiculo})
        ),
        ui.panel_main(
            ui.h4("Pronóstico de tránsito histórico"),
            output_widget("grafica_forecast"),
            ui.h4("Resumen por tipo de vehículo y año"),
            output_widget("grafica_vehiculos"),
            ui.h4("Vista de datos"),
            ui.output_data_frame("tabla_datos")
        )
    )
)

# Lógica
def server(input, output, session):
    @reactive.Calc
    def datos_filtrados():
        return df[(df["AÑO"] == int(input.anio())) & (df["MES"] == int(input.mes()))]

    @output
    @render_widget
    def grafica_forecast():
        df_hist = df[(df["AÑO"] < 2025) & (~df[input.vehiculo()].isna())].groupby(["AÑO", "MES"])[input.vehiculo()].sum().reset_index()
        df_hist["FECHA"] = pd.to_datetime(df_hist["AÑO"].astype(str) + "-" + df_hist["MES"].astype(str))
        fig = px.line(df_hist, x="FECHA", y=input.vehiculo(), title=f"Histórico de {input.vehiculo()}")
        return fig

    @output
    @render_widget
    def grafica_vehiculos():
        df_anual = df[df["AÑO"] == int(input.anio())]
        resumen = df_anual.groupby("TIPO")[[v for v in tipos_vehiculo]].sum().reset_index()
        resumen_melt = resumen.melt(id_vars="TIPO", var_name="Vehículo", value_name="Cantidad")
        fig = px.bar(resumen_melt, x="Vehículo", y="Cantidad", color="TIPO", barmode="group", title="Distribución por tipo de vehículo")
        return fig

    @output
    @render.data_frame
    def tabla_datos():
        return render.DataGrid(datos_filtrados())

app = App(app_ui, server)
