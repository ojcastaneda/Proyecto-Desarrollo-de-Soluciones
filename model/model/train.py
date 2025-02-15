from .model import Preprocessor, split_dataset
from pandas import read_csv, DataFrame, Series
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from mlflow import log_metric, log_param, set_experiment, start_run
from mlflow.sklearn import log_model
from numpy import ndarray
import random

random_seed = 79
random.seed(random_seed)


def report(
    pipeline: Pipeline,
    predictions: ndarray | tuple[ndarray, ndarray],
    target: Series,
    experiment: str,
):
    print(classification_report(target, predictions, digits=4))
    set_experiment(experiment)
    with start_run():
        log_param("steps", pipeline.get_params(False)["steps"])
        metrics: dict[str, dict[str, float]] = classification_report(
            target, predictions, digits=4, output_dict=True
        )
        metrics["Abandonó"] = metrics.pop("1")
        metrics["Culminó"] = metrics.pop("0")
        log_metric("accuracy", metrics.pop("accuracy"))
        for category in metrics:
            for metric in metrics[category]:
                log_metric(f"{category}__{metric}", metrics[category][metric])
        log_model(pipeline, "model")


def load_data(path: str):
    data = read_csv(path, on_bad_lines="warn", encoding="utf-8")
    train, test = train_test_split(data, test_size=0.2, random_state=random_seed)
    dataset_cleanup(train)
    dataset_cleanup(test)
    return train, test


def grid_report(grid: GridSearchCV, dataset: DataFrame, experiment: str):
    pipeline: Pipeline = grid.best_estimator_
    x, y = split_dataset(dataset)
    print(grid.best_params_)
    report(pipeline, pipeline.predict(x), y, experiment)
    return pipeline


def cross_validation(
    additional_layers: list[tuple[str, BaseEstimator]],
    dataset: DataFrame,
    parameters: dict,
    metric: str = "recall",
    include_all: bool = False,
    include_bias: bool = False,
):
    x, y = split_dataset(dataset)
    transformations = ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", drop="if_binary"),
                make_column_selector(dtype_include=object),
            ),
        ],
        remainder="passthrough",
        verbose_feature_names_out=False,
    )
    pipeline = Pipeline(
        [
            ("preprocessor", Preprocessor(include_all, include_bias)),
            ("transformations", transformations),
            *additional_layers,
        ]
    )
    grid = GridSearchCV(pipeline, parameters, verbose=0, scoring=metric, cv=5, n_jobs=5)
    grid.fit(x, y)
    return grid, DataFrame(grid.cv_results_).sort_values(
        by="rank_test_score", ascending=True
    ).head(5)


def dataset_cleanup(dataset: DataFrame):
    conditions = (
        (dataset["Grupo Etario"] != "<No Registra>")
        & (dataset["Tipo de Vivienda"] != "<No Registra>")
        & (dataset["Régimen de tenencia Vivienda"] != "<No Registra>")
        & (
            dataset["Situación Final frente al proceso"].isin(
                ["Culminado", "Fuera del Proceso"]
            )
        )
    )
    dataset.drop(index=dataset[~conditions].index, inplace=True)

