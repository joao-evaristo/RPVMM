import random


def ordered_crossover(parent1, parent2):
    cut_points = random.sample(range(len(parent1)), 2)
    cut_point1, cut_point2 = min(cut_points), max(cut_points)
    child1 = [-1] * len(parent1)
    child2 = [-1] * len(parent1)
    child1[cut_point1 : cut_point2 + 1] = parent2[cut_point1 : cut_point2 + 1]
    child2[cut_point1 : cut_point2 + 1] = parent1[cut_point1 : cut_point2 + 1]
    fill_values(child1, parent1)
    fill_values(child2, parent2)

    return child1, child2


def fill_values(child, parent):
    _ = [value for value in parent if value not in child]
    child[:] = [value if child[i] == -1 else child[i] for i, value in enumerate(parent)]
