import pickle

import sparse


def save_score_matrix(score_matrix_p: str, score_matrix: sparse.COO) -> None:
    with open(score_matrix_p, 'wb') as fh:
        pickle.dump(score_matrix, fh)


def load_score_matrix(score_matrix_p: str) -> sparse.COO:
    with open(score_matrix_p, 'rb') as fh:
        return pickle.load(fh)
