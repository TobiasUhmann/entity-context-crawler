from ryn.graphs import split


# @st.cache(allow_output_mutation=True)
def load_dataset(dataset_dir: str) -> split.Dataset:
    """
    :param dataset_dir: Path to Ryn dataset directory
    """

    return split.Dataset.load(dataset_dir)
