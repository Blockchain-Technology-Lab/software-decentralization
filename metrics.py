from math import log
import numpy as np


def compute_nakamoto_coefficient(commit_distribution):
    return compute_tau_index(commit_distribution, 0.5)


def compute_tau_index(commit_distribution, threshold):
    """
    Calculates the tau-decentralization index of a distribution of commits
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :param threshold: float, the parameter of the tau-decentralization index, i.e. the threshold for the power
    ratio that is captured by the index (e.g. 0.66 for 66%)
    :returns: int that corresponds to the tau index of the given distribution, or None if there were no commits
    """
    total_commits = sum(commit_distribution)
    if total_commits == 0:
        return None
    tau_index, power_ratio_covered = 0, 0
    for commit_amount in commit_distribution:
        if power_ratio_covered >= threshold:
            break
        tau_index += 1
        power_ratio_covered += commit_amount / total_commits
    return tau_index


def compute_gini(commit_distribution):
    """
    Calculates the Gini coefficient of a distribution of commits to entities
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :returns: a float that represents the Gini coefficient of the given distribution or None if the data is empty
    """
    if sum(commit_distribution) == 0:
        return None
    array = np.array(commit_distribution)
    return gini(array)


def gini(array):
    """
    Calculates the Gini coefficient of a distribution
    Source: https://github.com/oliviaguest/gini
    :param array: a numpy array with entities and the commits they have produced
    :returns: a float that represents the Gini coefficient of the given distribution
    """
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


def compute_herfindahl_hirschman_index(commit_distribution):
    """
    Calculates the Herfindahl-Hirschman index (HHI) of a distribution of commits to entities
    From investopedia: The HHI is calculated by squaring the market share of each firm competing in a market and then
    summing the resulting numbers. It can range from close to 0 to 10,000, with lower values indicating a less
    concentrated market. The U.S. Department of Justice considers a market with an HHI of less than 1,500 to be a
    competitive marketplace, an HHI of 1,500 to 2,500 to be a moderately concentrated marketplace,
    and an HHI of 2,500 or greater to be a highly concentrated marketplace.
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :return: float between 0 and 10,000 that represents the HHI of the given distribution or None if the data is empty
    """
    total_commits = sum(commit_distribution)
    if total_commits == 0:
        return None

    hhi = 0
    for num_commits in commit_distribution:
        hhi += pow(100 * num_commits / total_commits, 2)

    return hhi


def compute_entropy(commit_distribution, alpha=1):
    """
    Calculates the entropy of a distribution of commits to entities
    Pi is the relative frequency of each entity.
    Renyi entropy: 1/(1-alpha) * log2 (sum (Pi**alpha))
    Shannon entropy (alpha=1): −sum P(Si) log2 (Pi)
    Min entropy (alpha=-1): -log max Pi
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :param alpha: the entropy parameter (depending on its value the corresponding entropy measure is used)
    :returns: a float that represents the entropy of the data or None if the data is empty
    """
    all_commits = sum(commit_distribution)
    if all_commits == 0:
        return None
    if alpha == 1:
        entropy = 0
        for value in commit_distribution:
            rel_freq = value / all_commits
            if rel_freq > 0:
                entropy -= rel_freq * log(rel_freq, 2)
    else:
        if alpha == -1:
            entropy = - log(max(commit_distribution)/all_commits, 2)
        else:
            sum_freqs = 0
            for entry in commit_distribution:
                sum_freqs += pow(entry/all_commits, alpha)
            entropy = log(sum_freqs, 2) / (1 - alpha)

    return entropy


def compute_total_entities(commit_distribution):
    """
    Calculates the total number of entities in a distribution of balances
    :param entries: list of tuples (balance, ), sorted by balance in descending order, where balance is a numeric type (int or float)
    :param circulation: int, the total amount of tokens in circulation
    :returns: int that represents the total number of entities in the given distribution
    """
    return len(commit_distribution)


def compute_max_power_ratio(commit_distribution):
    """
    Calculates the maximum power ratio of a distribution of balances
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :returns: float that represents the maximum power ratio among all commit producers (0 if there weren't any)
    """
    total_commits = sum(commit_distribution)
    return commit_distribution[0] / total_commits if total_commits else 0


def compute_theil_index(commit_distribution):
    """
    Calculates the Thiel index of a distribution of commits to entities
    :param commit_distribution: a list of integers, each being the commits that an entity has produced, sorted in descending order
    :returns: float that represents the Thiel index of the given distribution
    """
    n = len(commit_distribution)
    if n == 0:
        return 0
    total_commits = sum(commit_distribution)
    mu = total_commits / n
    theil = 0
    for ncommits in commit_distribution:
        x = ncommits / mu
        if x > 0:
            theil += x * log(x)
    theil /= n
    return theil
