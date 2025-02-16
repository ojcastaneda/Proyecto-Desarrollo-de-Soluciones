from lime.lime_tabular import LimeTabularExplainer
from matplotlib.pyplot import close, figure
from pandas import DataFrame
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.tree import plot_tree
from .model import split_dataset


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
