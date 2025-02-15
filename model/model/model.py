from joblib import dump, load
from pandas import DataFrame
from pathlib import Path
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

target_column = "Situación Final frente al proceso"

bias_column = "DesagregadoDesembolsoBIE"

main_columns = [
    "Línea de FpT para el Máx. Nivel",
    "OcupacionEconomica",
    "Desembolso BIE",
    "Estado de la vinculación ASS",
    "Posee Cónyuge o Compañero(a)?",
]

secondary_columns = [
    "Tipo de Desmovilización",
    "Grupo Etario",
    "Sexo",
    "Nivel Educativo",
    "Máximo Nivel FpT Reportado",
    "Tipo de ASS Vinculada",
    "N° de Hijos",
    "Total Integrantes grupo familiar",
    "Tipo de Vivienda",
    "Régimen de tenencia Vivienda",
    "Posee Serv. Públicos Básicos",
    "Régimen de salud",
]


class Preprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, include_all: bool, include_bias: bool) -> None:
        super().__init__()
        self.include_all = include_all
        self.include_bias = include_bias
        self.options = {}

    def fit(self, x: DataFrame, y: DataFrame | None = None):
        columns = main_columns + secondary_columns
        for column in x:
            if column not in columns:
                continue
            self.options[column] = x[column].unique().tolist()
        return self

    def transform(self, x: DataFrame, y: DataFrame | None = None):
        columns = main_columns.copy()
        if self.include_all:
            columns += secondary_columns
            if self.include_bias:
                columns.append(bias_column)
        x.drop(columns=[col for col in x if col not in columns], inplace=True)
        x.replace(
            {
                "OcupacionEconomica": {"   ": "<No Registra>"},
                "Posee Cónyuge o Compañero(a)?": {"<No Registra>": "<No Aplica>"},
                "Línea de FpT para el Máx. Nivel": {"<No Registra>": "<No Aplica>"},
                "Máximo Nivel FpT Reportado": {
                    "Técnico Laboral": "Técnico",
                    "Técnico Profesional": "Técnico",
                    "Técnico Laboral por Competencias": "Técnico",
                    "Especialización Técnica": "Técnico",
                    "Especialización Tecnológica": "Tecnológico",
                    "Operario": "Otro",
                    "Auxiliar": "Otro",
                    "Certificación por Evaluación de Competencias": "Otro",
                },
                "Grupo Etario": {
                    "Entre 18 y 25 años": "Entre 18 y 40 años",
                    "Entre 26 y 40 años": "Entre 18 y 40 años",
                },
                "Régimen de tenencia Vivienda": {
                    "Propia, totalmente pagada": "Propia",
                    "Propia, la están pagando": "Propia",
                    "Sana posesión con título": "Propia",
                    "Es usufructo": "Con permiso del propietario, sin pago alguno",
                    "Familiar": "Con permiso del propietario, sin pago alguno",
                    "Posesión sin título (ocupante de hecho) o propiedad colectiva": "Otra",
                    "Otra forma de tenencia  (posesión sin título, ocupante de hecho, propiedad colectiva, etc)": "Otra",
                },
                "Tipo de Vivienda": {
                    "Casa-Lote": "Casa",
                    "Cuarto(s)": "Habitación",
                    "Rancho": "Finca",
                    "Vivienda (casa) indígena": "Casa",
                    "Otro tipo de vivienda (carpa, tienda, vagón, embarcación, cueva, refugio natural, puente, calle, etc.)": "Otro",
                },
                "N° de Hijos": {-2: -1},
            },
            inplace=True,
        )
        if self.include_all:
            x["Sexo"] = x["Sexo"].str.upper()
        return x


def load_model(path: str):
    if not path.endswith(".pkl"):
        path += ".pkl"
    return load(path)


def save_model(model: Pipeline, path: str):
    if not path.endswith(".pkl"):
        path += ".pkl"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    dump(model, path)


def split_dataset(dataset: DataFrame):
    dataset = dataset.copy()
    y = (dataset["Situación Final frente al proceso"] == "Fuera del Proceso").astype(
        int
    )
    dataset.drop(columns=["Situación Final frente al proceso"], inplace=True)
    return dataset, y
