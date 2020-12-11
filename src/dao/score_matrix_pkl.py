import pickle

import sparse


def save_score_matrix(score_matrix_pkl: str, score_matrix: sparse.COO) -> None:
    with open(score_matrix_pkl, 'wb') as fh:
        pickle.dump(score_matrix, fh)


def load_score_matrix(score_matrix_pkl: str) -> sparse.COO:
    with open(score_matrix_pkl, 'rb') as fh:
        return pickle.load(fh)
