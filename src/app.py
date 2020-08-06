import os
import random
import streamlit as st

from collections import Counter
from ryn.graphs.split import Dataset

from eval.evaluator import Evaluator
from eval.model import Model


def main():
    st.title('Evaluate relation predictions')

    #
    # Sidebar
    #

    random_seed = st.sidebar.number_input('Random seed', value=0, format='%d')
    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    random.seed(random_seed)

    #
    # Load data
    #

    with st.spinner('Loading dataset...'):
        dataset_dir = 'data/oke.fb15k237_30061990_50'
        dataset = Dataset.load(dataset_dir)
    st.success('Dataset loaded')

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.ow_valid.triples}

    all_triples = list(cw_triples | ow_triples)

    #
    # Rank triples
    #

    head_counter = Counter([head for head, _, _ in all_triples])
    tail_counter = Counter([tail for _, tail, _ in all_triples])
    rel_counter = Counter([rel for _, _, rel in all_triples])

    all_triples.sort(key=lambda t: (head_counter[t[0]] + tail_counter[t[1]]) * rel_counter[t[2]], reverse=True)

    #
    # Create model
    #

    model = Model(all_triples)

    #
    # Evaluate model
    #

    some_ow_entities = random.sample(ow_entities, 10)
    evaluator = Evaluator(model, ow_triples, some_ow_entities)

    with st.spinner('Evaluating model...'):
        total_result = evaluator.run()
    st.success('Model evaluated')

    results, mAP = total_result.results, total_result.map

    for ow_entity, result in zip(some_ow_entities, results):
        pred_ow_triples = result.pred_ow_triples
        precision = result.precision
        recall = result.recall
        f1 = result.f1
        ap = result.ap

        pred_cw_entity = result.pred_cw_entity
        pred_ow_triples_hits = result.pred_ow_triples_hits

        output = '\n'
        output += ow_entity + ' -> ' + (pred_cw_entity if pred_cw_entity is not None else '<None>') + '\n'
        output += 50 * '-' + '\n'

        count = 0
        for triple, hit in zip(pred_ow_triples, pred_ow_triples_hits):
            if count == 20:
                break
            head, tail, rel = triple
            hit_marker = '+' if hit else ' '
            output += '{} {:30} {:30} {}\n'.format(
                hit_marker,
                truncate('[{}] {}'.format(head_counter[head], head), 28),
                truncate('[{}] {}'.format(tail_counter[tail], tail), 28),
                '[{}] {}'.format(rel_counter[rel], rel))
            count += 1
        if len(pred_ow_triples) - count > 0:
            output += '[{} more hidden]'.format(len(pred_ow_triples) - count) + '\n'
        output += 50 * '-' + '\n'
        output += '{:20} {:.2f}'.format('Precision', precision) + '\n'
        output += '{:20} {:.2f}'.format('Recall', recall) + '\n'
        output += '{:20} {:.2f}'.format('F1-Score', f1) + '\n'
        output += '{:20} {:.2f}'.format('Average Precision', ap) + '\n'

        st.markdown('```' + output + '```')

    st.write()
    st.write('mAP = ', mAP)


def truncate(str, max_len):
    return (str[:max_len - 3] + '...') if len(str) > max_len else str


if __name__ == '__main__':
    main()
