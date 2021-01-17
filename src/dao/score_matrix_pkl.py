import pickle

import sparse


def save_score_matrix(score_matrix_pkl: str, score_matrix: sparse.COO) -> None:
    data = {'version': 2, 'score_matrix': score_matrix}

    with open(score_matrix_pkl, 'wb') as f:
        pickle.dump(data, f)


def load_score_matrix(score_matrix_pkl: str) -> sparse.COO:
    with open(score_matrix_pkl, 'rb') as f:
        data = pickle.load(f)

    return data['score_matrix']
