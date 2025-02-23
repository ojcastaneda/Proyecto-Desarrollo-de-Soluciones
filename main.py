from streamlit import (
    button,
    cache_resource,
    columns,
    toggle,
    plotly_chart,
    selectbox,
    slider,
    set_page_config,
    title,
)
from pandas import DataFrame
from plotly.subplots import make_subplots
from plotly.graph_objects import Bar
from model.model import load_model
from sklearn.pipeline import Pipeline

page_title = "Análisis de Factores de Riesgo que influyen en la deserción de desmovilizados que han ingresado al proceso de reintegración"

set_page_config(page_title)
title(page_title)


@cache_resource
def load_models():
  return load_model(f"./simple.pkl"), load_model(f"./complete.pkl")


def predict(model: Pipeline):
  fig = make_subplots()
  fig.add_trace(
      Bar(
          x=["Culminará el proceso", "Abandonará el proceso"],
          y=model.predict_proba(
              DataFrame({key: [value] for key, value in data.items()})
          )[0],
      )
  )
  plotly_chart(fig, use_container_width=True)


simple_model, complete_model = load_models()
data = {}


def select_variable(label: str, variable: str):
  data[variable] = selectbox(label, simple_model.steps[0][1].options[variable])


simple_inputs = columns(2)
with simple_inputs[0]:
  select_variable(
      "Línea de FpT para el Máximo Nivel", "Línea de FpT para el Máx. Nivel"
  )
  select_variable("¿Desembolsó el BIE?", "Desembolso BIE")
with simple_inputs[1]:
  select_variable("Ocupacion económica", "OcupacionEconomica")
  select_variable("Estado de la vinculación ASS", "Estado de la vinculación ASS")
select_variable("Posee Cónyuge o Compañero(a)?", "Posee Cónyuge o Compañero(a)?")
with columns(3)[1]:
  use_complete = toggle("Usar predicción detallada")
if use_complete:
  inputs = columns(2)
  with inputs[0]:
    select_variable("Grupo Etario", "Grupo Etario")
    select_variable("Nivel Educativo", "Nivel Educativo")
    select_variable("Posee Serv. Públicos Básicos", "Posee Serv. Públicos Básicos")
    select_variable("Régimen de tenencia Vivienda", "Régimen de tenencia Vivienda")
    select_variable("Tipo de ASS Vinculada", "Tipo de ASS Vinculada")
    data["N° de Hijos"] = slider("Número de hijos", -1, 10, (1))
  with inputs[1]:
    select_variable("Sexo", "Sexo")
    select_variable("Máximo Nivel FpT Reportado", "Máximo Nivel FpT Reportado")
    select_variable("Régimen de salud", "Régimen de salud")
    select_variable("Tipo de Vivienda", "Tipo de Vivienda")
    select_variable("Tipo de Desmovilización", "Tipo de Desmovilización")
    data["Total Integrantes grupo familiar"] = slider(
        "Integrantes grupo familiar", -1, 20, (1)
    )
with columns(3)[1]:
  graph = button("Realizar predicción", use_container_width=True)
if graph:
  predict(complete_model if use_complete else simple_model)
