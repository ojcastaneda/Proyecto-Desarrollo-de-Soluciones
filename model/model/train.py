from .analyze import generate_bias_detection_datasets
from .model import Preprocessor, split_dataset
from aif360.algorithms.preprocessing import Reweighing
from pandas import read_csv, DataFrame, Series
from sklearn.base import BaseEstimator, clone
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


def test_report_umbral(
    pipeline: Pipeline, dataset: DataFrame, umbral: float, experiment
):
    x, y = split_dataset(dataset)
    report(
        pipeline, (pipeline.predict_proba(x)[:, 1] >= umbral).astype(int), y, experiment
    )


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


def train_unbiased_model(
    pipeline: Pipeline,
    train_dataset: DataFrame,
    test_dataset: DataFrame,
    experiment: str,
):
    x, y = split_dataset(train_dataset)
    unbiased_pipeline = Pipeline(clone(pipeline).steps[:-1])
    unbiased_pipeline.fit(x, y)
    balanced_train, _, feature_names = generate_bias_detection_datasets(
        unbiased_pipeline, train_dataset, test_dataset, ["Sexo", "Grupo Etario"]
    )
    sex_bias_fixer = Reweighing([{"Sexo_MASCULINO": 1}], [{"Sexo_MASCULINO": 0}])
    balanced_train = sex_bias_fixer.fit_transform(balanced_train)
    age_bias_fixer = Reweighing(
        [{"Grupo Etario_Entre 18 y 40 años": 1}],
        [{"Grupo Etario_Entre 41 y 60 años": 1}, {"Grupo Etario_Mayor de 60 años": 1}],
    )
    balanced_train = age_bias_fixer.fit_transform(balanced_train)
    target = balanced_train.labels
    balanced_train = DataFrame(
        balanced_train.features, columns=balanced_train.feature_names
    )
    extra_columns = [
        col
        for col in feature_names
        if col not in unbiased_pipeline[-1].get_feature_names_out()
    ]
    balanced_train.drop(extra_columns, axis=1, inplace=True)
    model = clone(pipeline.steps[-1][1])
    model.fit(balanced_train.values, target)
    unbiased_pipeline.steps.append((pipeline.steps[-1][0], model))
    x, y = split_dataset(test_dataset)
    report(pipeline, pipeline.predict(x), y, experiment)
    return unbiased_pipeline
