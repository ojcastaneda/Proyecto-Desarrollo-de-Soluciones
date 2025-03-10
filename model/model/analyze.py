from aif360.datasets import BinaryLabelDataset
from aif360.metrics import ClassificationMetric
from lime.lime_tabular import LimeTabularExplainer
from matplotlib.pyplot import close, figure
from pandas import DataFrame
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import plot_tree
from .model import Preprocessor, split_dataset, target_column


def check_folder(folder):
    path = Path(folder).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _extract_model_data(pipeline: Pipeline, test_dataset: DataFrame):
    x, _ = split_dataset(test_dataset)
    model = pipeline[-1]
    x = DataFrame(pipeline[:-1].transform(x).todense())
    feature_names = pipeline[-2].get_feature_names_out()
    return model, feature_names, x, ["Terminará", "Abandonará"]


def analyze_variables(pipeline: Pipeline, test_dataset: DataFrame, output_folder: str):
    path = Path(output_folder).mkdir(parents=True, exist_ok=True)
    model, feature_names, x, class_names = _extract_model_data(pipeline, test_dataset)
    explainer = LimeTabularExplainer(
        x.values, feature_names=feature_names, kernel_width=5, class_names=class_names
    )
    predict_fn = lambda x: model.predict_proba(x).astype(float)
    negative = explainer.explain_instance(x.loc[[0]].values[0], predict_fn)
    path = check_folder(output_folder)
    negative.save_to_file(path.joinpath("negative.html"), show_all=False)
    positive = explainer.explain_instance(x.loc[[31]].values[0], predict_fn)
    positive.save_to_file(path.joinpath("positive.html"), show_all=False)


def print_tree(pipeline: Pipeline, test_dataset: DataFrame, output_folder: str):
    model, feature_names, _, class_names = _extract_model_data(pipeline, test_dataset)
    tree_figure = figure(figsize=(9, 2), dpi=500)
    path = check_folder(output_folder)
    plot_tree(
        model,
        feature_names=feature_names,
        class_names=class_names,
        filled=True,
        fontsize=3,
        rounded=True,
        max_depth=2,
    )
    tree_figure.savefig(path.joinpath("tree.png"))
    close()


def detect_dataset_bias(
    pipeline: Pipeline,
    dataset: DataFrame,
    variables: list[str],
    one_hot: OneHotEncoder | None = None,
):
    x, y = split_dataset(dataset)
    preprocessor = Preprocessor(True, False)
    feature_names = pipeline[-1].get_feature_names_out()
    variables_data = preprocessor.transform(x).reset_index(drop=True)[variables]
    transformed = DataFrame(pipeline.transform(x).todense(), columns=feature_names)
    transformed[target_column] = y.reset_index(drop=True)
    if one_hot is None:
        one_hot = OneHotEncoder(handle_unknown="ignore", drop="if_binary")
        one_hot.fit(variables_data)
    protected = one_hot.get_feature_names_out()
    variables_data = DataFrame(
        one_hot.transform(variables_data).todense(), columns=protected
    )
    missing_columns = variables_data.columns.difference(transformed.columns)
    return (
        BinaryLabelDataset(
            df=transformed.join(variables_data[missing_columns]),
            label_names=[target_column],
            protected_attribute_names=protected,
        ),
        one_hot,
    )


def generate_bias_detection_datasets(
    pipeline: Pipeline,
    train_dataset: DataFrame,
    test_dataset: DataFrame,
    variables: list[str],
):
    balanced_train, one_hot = detect_dataset_bias(pipeline, train_dataset, variables)
    balanced_test, _ = detect_dataset_bias(pipeline, test_dataset, variables, one_hot)
    return balanced_train, balanced_test, one_hot.get_feature_names_out()


def check_bias(
    pipeline: Pipeline,
    train_dataset: DataFrame,
    test_dataset: DataFrame,
    variables: list[str],
):
    x, _ = split_dataset(test_dataset)
    for variable in variables:
        _, balanced_test, feature_names = generate_bias_detection_datasets(
            pipeline[:-1], train_dataset, test_dataset, [variable]
        )
        labeled_test = balanced_test.copy()
        labeled_test.labels = pipeline.predict(x)
        for name in feature_names:
            metric_test = ClassificationMetric(
                balanced_test,
                labeled_test,
                privileged_groups=[{name: 1}],
                unprivileged_groups=[{name: 0}],
            )
            print(
                f"{name} | Statistical Parity Difference: ",
                metric_test.statistical_parity_difference(),
            )
            print(
                f"{name} | Equal Opportunity Difference: ",
                metric_test.equal_opportunity_difference(),
            )
