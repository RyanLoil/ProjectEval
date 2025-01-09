import copy

from codebleu import calc_codebleu
import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.optimize import linear_sum_assignment
from utils import string_similarity

def jonker_volgenant_algorithm(cost_matrix):
    """
    Implements the Jonker-Volgenant Algorithm for solving the assignment problem to maximize weight.

    :param cost_matrix: 2D numpy array representing the cost matrix.
    :return: A tuple containing the maximum cost and the assignment as a list of (row, col) pairs.
    """
    cost_matrix = np.array(cost_matrix)
    original_matrix = copy.deepcopy(cost_matrix)
    cost_matrix = - cost_matrix

    print(original_matrix)

    def find_optimal_assignment(matrix):
        row_ind, col_ind = linear_sum_assignment(matrix)
        return list(zip(row_ind, col_ind))

    assignment = find_optimal_assignment(cost_matrix)

    total_cost = sum(original_matrix[r, c] for r, c in assignment)
    return total_cost, assignment


def sentence_transformer_calc(data:list[str], reference:list[str], model: str = "all-MiniLM-L6-v2"):
    """
    Sentence Transformer calculator function.
    :param data: the test data.
    :param reference: the reference (canonical solution).
    :param model: default all-MiniLM-L6-v2.
    :return: Best Sentence Transformer score, Assignment of selection.
    """
    mt = data + reference
    m = len(data)
    n = len(reference)
    model = SentenceTransformer(model)
    embeddings = model.encode(mt)
    similarities = model.similarity(embeddings, embeddings)
    similarities_matrix = similarities[m:m + n, :m]  # the cost matrix for JV Algorithm
    best_score, assignment = jonker_volgenant_algorithm(similarities_matrix)
    return round(best_score / n, 3), assignment


def codebleu_calc(data:list[str], reference:list[str], language:str="python", mode:str="codebleu"):
    """
    Codebleu calculator function. Input should be file level.
    :param data: the test data.
    :param reference: the reference (canonical solution).
    :param language: the data's language, default python.
    :param mode: default codebleu. Support ngram_match_score, weighted_ngram_match_score, syntax_match_score and dataflow_match_score @https://github.com/k4black/codebleu
    :return: Best Codebleu score, Assignment of selection.
    """
    m = len(data)
    n = len(reference)
    similarities_matrix = [[0 for _ in range(n)] for __ in range(m)]
    for i, d in enumerate(data):
        for j, r in enumerate(reference):
            similarities_matrix[i][j] = calc_codebleu([r], [d], language)["codebleu"]

    best_score, assignment = jonker_volgenant_algorithm(similarities_matrix)
    return round(best_score / n, 3), assignment



def levenshtein_calc(data:dict, reference:dict, ):
    """

    :param data: One project's parameter value DICTIONARY transform from parameters.json
    :param reference:  One project's parameter value DICTIONARY transform from canonical parameters.json
    :return: Best Levenshtein score.
    """
    counter = 0
    score = 0
    similarities = {}
    for page in reference:
        for function in reference[page]:
            if page not in data:
                counter += len(reference[page][function])
                continue
            if function not in data[page]:
                counter += len(reference[page][function])
                continue
            temp_dict = {}
            for parameter in data[page][function]:
                temp_dict[parameter["name"]] = parameter["answer"]
            for parameter in reference[page][function]:
                if parameter["name"] not in temp_dict:
                    counter += 1
                    continue
                similarity = string_similarity(parameter["answer"], temp_dict[parameter["name"]])
                score += similarity
                similarities.setdefault(page, {})
                similarities[page].setdefault(function, {})
                similarities[page][function][parameter["name"]] = similarity
                counter += 1
    return score/counter, similarities


METHOD_DICTIONARY = {
    "sentence_transformer": sentence_transformer_calc,
    "codebleu": codebleu_calc,
    "levenshtein": levenshtein_calc
}
