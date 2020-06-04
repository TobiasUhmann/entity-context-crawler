import matplotlib.pyplot as plt
import sqlite3

from collections import Counter
from elasticsearch import Elasticsearch
from matplotlib.widgets import Slider

MATCHES_DB = 'data/matches.db'


def select_entities(conn, limit):
    sql = '''
        SELECT DISTINCT entity
        FROM matches
        LIMIT ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (limit,))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def select_contexts(conn, entity, size, limit):
    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]
        
        SELECT substr(content,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(content)))
        FROM docs INNER JOIN matches ON docs.title = matches.doc
        WHERE entity = ?
        LIMIT ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, entity, limit))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def plot_statistics(statistics, sort=False):
    """
    Plot bar chart showing the absolute frequency of the entities (in descending order). Limited to
    the 100 most frequent entities. Interrupts the program.
    """

    statistics_list = list(statistics.items())
    top_statistics = sorted(statistics_list, key=lambda item: item[1], reverse=True)[:200] if sort else statistics_list[:200]
    entities = [item[0] for item in top_statistics]
    frequencies = [item[1] for item in top_statistics]

    visible_bars = 10

    ax_bar_chart = plt.axes([0.1, 0.2, 0.8, 0.6])
    plt.bar(entities[:visible_bars], frequencies[:visible_bars])
    plt.gca().set_ylim([0, 1])

    #
    # Sliders for scrolling through entities and showing more/less entities at a time. Update
    # chart on slider change.
    #

    def update(val):
        scroll = int(scroll_slider.val)  # new scroll position
        bars = int(visible_bars_slider.val)  # new visible bars

        ax_bar_chart.clear()
        plt.sca(ax_bar_chart)
        plt.xticks(rotation=90)
        plt.gca().set_ylim([0, 1])

        ax_bar_chart.bar(entities[scroll:(scroll + bars)],
                         frequencies[scroll:(scroll + bars)])

    ax_scroll = plt.axes([0.1, 0.9, 0.8, 0.03])
    scroll_slider = Slider(ax_scroll, '', 0, len(entities), valfmt='%d')
    scroll_slider.on_changed(update)

    ax_span = plt.axes([0.1, 0.85, 0.8, 0.03])
    visible_bars_slider = Slider(ax_span, '', 10, 100, valinit=visible_bars, valfmt='%d')
    visible_bars_slider.on_changed(update)

    #
    # Initial plotting. Updated on slider change.
    #

    plt.sca(ax_bar_chart)
    plt.xticks(rotation=90)
    plt.show()


class EntityLinker:
    matches_db: str  # path/to/matches.db

    def __init__(self, matches_db):
        self.matches_db = matches_db

    def test(self):
        es = Elasticsearch()
        with sqlite3.connect(self.matches_db) as matches_conn:
            all_test_contexts = {}

            entities = select_entities(matches_conn, limit=100)
            for id, entity in enumerate(entities):
                contexts = select_contexts(matches_conn, entity, size=100, limit=100)
                print(contexts)
                cropped_contexts = [context[context.find(' ') + 1: context.rfind(' ')] for context in contexts]
                masked_contexts = [context.replace(entity, '') for context in cropped_contexts]

                train_contexts = masked_contexts[:int(0.7 * len(masked_contexts))]
                test_contexts = masked_contexts[int(0.7 * len(masked_contexts)):]
                all_test_contexts[entity] = test_contexts

                doc = {'entity': entity, 'context': ' '.join(train_contexts)}
                es.index(index="sentence-sampler-index", id=id, body=doc)
                es.indices.refresh(index="sentence-sampler-index")

            hit_counter = Counter()
            hit_counter_right = Counter()

            for entity in all_test_contexts:
                for test_context in all_test_contexts[entity]:
                    print(entity, '#', test_context)

                    res = es.search(index="sentence-sampler-index", body={"query": {"match": {'context': test_context}}})
                    print("Got %d Hits:" % res['hits']['total']['value'])
                    hits = res['hits']['hits']
                    for hit in hits:
                        print(hit['_score'], hit['_source'])
                        break

                    if len(hits) > 0:
                        top_hit = res['hits']['hits'][0]
                        hit_counter[entity] += 1
                        if top_hit['_source']['entity'] == entity:
                            print('+++')
                            hit_counter_right[entity] += 1

                    print()

            for entity in entities:
                print('{0:30}{1:2} / {2:2}'.format(entity, hit_counter_right[entity], hit_counter[entity]))

            statistics = {'{0} ({1})'.format(entity, hit_counter[entity]): hit_counter_right[entity] / hit_counter[entity]
                          for entity in entities if hit_counter[entity] > 0}
            plot_statistics(statistics)
            plot_statistics(statistics, sort=True)



def main():
    entity_linker = EntityLinker(MATCHES_DB)
    entity_linker.test()


if __name__ == '__main__':
    main()
