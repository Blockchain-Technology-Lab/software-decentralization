from math import log
import numpy as np


def compute_nakamoto_coefficient(block_distribution):
    return compute_tau_index(block_distribution, 0.5)


def compute_tau_index(block_distribution, threshold):
    """
    Calculates the tau-decentralization index of a distribution of blocks
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :param threshold: float, the parameter of the tau-decentralization index, i.e. the threshold for the power
    ratio that is captured by the index (e.g. 0.66 for 66%)
    :returns: int that corresponds to the tau index of the given distribution, or None if there were no blocks
    """
    total_blocks = sum(block_distribution)
    if total_blocks == 0:
        return None
    tau_index, power_ratio_covered = 0, 0
    for block_amount in block_distribution:
        if power_ratio_covered >= threshold:
            break
        tau_index += 1
        power_ratio_covered += block_amount / total_blocks
    return tau_index


def compute_gini(block_distribution):
    """
    Calculates the Gini coefficient of a distribution of blocks to entities
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :returns: a float that represents the Gini coefficient of the given distribution or None if the data is empty
    """
    if sum(block_distribution) == 0:
        return None
    array = np.array(block_distribution)
    return gini(array)


def gini(array):
    """
    Calculates the Gini coefficient of a distribution
    Source: https://github.com/oliviaguest/gini
    :param array: a numpy array with entities and the blocks they have produced
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


def compute_hhi(block_distribution):
    """
    Calculates the Herfindahl-Hirschman index of a distribution of blocks to entities
    From investopedia: The HHI is calculated by squaring the market share of each firm competing in a market and then
    summing the resulting numbers. It can range from close to 0 to 10,000, with lower values indicating a less
    concentrated market. The U.S. Department of Justice considers a market with an HHI of less than 1,500 to be a
    competitive marketplace, an HHI of 1,500 to 2,500 to be a moderately concentrated marketplace,
    and an HHI of 2,500 or greater to be a highly concentrated marketplace.
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :return: float between 0 and 10,000 that represents the HHI of the given distribution or None if the data is empty
    """
    total_blocks = sum(block_distribution)
    if total_blocks == 0:
        return None

    hhi = 0
    for num_blocks in block_distribution:
        hhi += pow(100 * num_blocks / total_blocks, 2)

    return hhi


def compute_entropy(block_distribution, alpha=1):
    """
    Calculates the entropy of a distribution of blocks to entities
    Pi is the relative frequency of each entity.
    Renyi entropy: 1/(1-alpha) * log2 (sum (Pi**alpha))
    Shannon entropy (alpha=1): −sum P(Si) log2 (Pi)
    Min entropy (alpha=-1): -log max Pi
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :param alpha: the entropy parameter (depending on its value the corresponding entropy measure is used)
    :returns: a float that represents the entropy of the data or None if the data is empty
    """
    all_blocks = sum(block_distribution)
    if all_blocks == 0:
        return None
    if alpha == 1:
        entropy = 0
        for value in block_distribution:
            rel_freq = value / all_blocks
            if rel_freq > 0:
                entropy -= rel_freq * log(rel_freq, 2)
    else:
        if alpha == -1:
            entropy = - log(max(block_distribution)/all_blocks, 2)
        else:
            sum_freqs = 0
            for entry in block_distribution:
                sum_freqs += pow(entry/all_blocks, alpha)
            entropy = log(sum_freqs, 2) / (1 - alpha)

    return entropy


def compute_total_entities(block_distribution):
    """
    Calculates the total number of entities in a distribution of balances
    :param entries: list of tuples (balance, ), sorted by balance in descending order, where balance is a numeric type (int or float)
    :param circulation: int, the total amount of tokens in circulation
    :returns: int that represents the total number of entities in the given distribution
    """
    return len(block_distribution)


def compute_max_power_ratio(block_distribution):
    """
    Calculates the maximum power ratio of a distribution of balances
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :returns: float that represents the maximum power ratio among all block producers (0 if there weren't any)
    """
    total_blocks = sum(block_distribution)
    return block_distribution[0] / total_blocks if total_blocks else 0


def compute_theil_index(block_distribution):
    """
    Calculates the Thiel index of a distribution of blocks to entities
    :param block_distribution: a list of integers, each being the blocks that an entity has produced, sorted in descending order
    :returns: float that represents the Thiel index of the given distribution
    """
    n = len(block_distribution)
    if n == 0:
        return 0
    total_blocks = sum(block_distribution)
    mu = total_blocks / n
    theil = 0
    for nblocks in block_distribution:
        x = nblocks / mu
        if x > 0:
            theil += x * log(x)
    theil /= n
    return theil
