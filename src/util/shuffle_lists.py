from random import shuffle


def shuffle_lists(*lists):
    table = list(zip(*lists))

    shuffle(table)

    return zip(*table)
