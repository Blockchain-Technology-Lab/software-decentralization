import csv
import json
import logging
import pathlib
from collections import defaultdict
from yaml import safe_load


logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
with open("config.yaml") as f:
    config = safe_load(f)


def get_config_data():
    """
    Reads the configuration data of the project. This data is read from a file named "confing.yaml" located at the
    root directory of the project.
    :returns: a dictionary of configuration keys and values
    """
    return config


def get_ledger_repos():
    """
    Retrieves the information about the repositories of the ledgers of interest.
    :returns: a dictionary where the keys are the names of the ledgers and each value is a list with the relevant
    repository names.
    """
    config = get_config_data()
    try:
        repos = config['repositories']
    except KeyError:
        repos = {}
        logging.warning('No repositories found in config.yaml. No data will be collected / analyzed.')
    return repos


def get_metrics():
    """
    Retrieves the list of metrics that are to be calculated.
    :returns: a list of strings, each corresponding to a metric
    """
    config = get_config_data()
    try:
        metrics = config['metrics']
    except KeyError:
        metrics = []
        logging.warning('No metrics found in config.yaml. No metrics will be calculated.')
    return metrics


def get_commits_per_sample_window_list():
    """
    Retrieves the numbers of commits per sample window that will be used for the analysis.
    :returns: a list of numbers that corresponds to the commits per sample window that will be
    used in the analysis. If none is found in the configuration file, it returns [None].
    """
    config = get_config_data()
    try:
        commits_per_sample_window_list = config['commits_per_sample_window']
    except KeyError:
        commits_per_sample_window_list = [None]
        logging.warning('No commits_per_sample_window found in config.yaml. Defaulting to using '
                        'entire history as a single sample).')
    return commits_per_sample_window_list


def get_contributor_types():
    """
    Retrieves the list of contributor types that will be considered in the analysis.
    :returns: a list of strings, each corresponding to a contributor type
    """
    config = get_config_data()
    try:
        contributor_types = config['contributor_types']
    except KeyError:
        contributor_types = []
        logging.warning('No contributor types found in config.yaml.')
    return contributor_types


def get_contribution_types():
    """
    Retrieves the contribution types that will be used for the analysis (e.g. number of commits).
    :returns: a list of strings, each corresponding to a contribution type
    """
    config = get_config_data()
    try:
        contribution_types = config['contribution_types']
    except KeyError:
        contribution_types = []
        logging.warning('No contribution types found in config.yaml.')
    return contribution_types


def get_refresh_data_flag():
    """
    Retrieves the flag that determines whether the commit data should be refreshed or not.
    :returns: a boolean that determines whether the data should be refreshed or not
    """
    config = get_config_data()
    try:
        refresh_data_flag = config['refresh_data']
    except KeyError:
        refresh_data_flag = False
        logging.warning('No refresh_data flag found in config.yaml. Defaulting to False.')
    return refresh_data_flag


def get_output_dir(output_type, contribution_type, contributor_type, commits_per_sample_window, data_type, mkdir=False):
    """
    Determines the output directory where the produced files will be saved.
    :param output_type: either "data" or "figures"
    :param contribution_type: one of the contribution types from config.yaml (e.g. number_of_commits)
    :param contributor_type: one of the contributor types from config.yaml (e.g. author)
    :param commits_per_sample_window: the number of commits per sample window used in the analysis
    :param data_type: either "commits_per_contributor" or "metrics"
    :param mkdir: boolean that determines whether the output directory should be created if it does not exist
    :returns: a pathlib.PosixPath object of the output directory
    """
    output_dir = pathlib.Path(f'output/{output_type}/by_{contribution_type}/per_{contributor_type}/per_{commits_per_sample_window}_commits'
                              f'/{data_type}')
    if mkdir:
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def read_commit_data(ledger, repo):
    """
    Reads the raw commit data for some repository associated with some ledger.
    :param ledger: string with the name of the ledger
    :param repo: string with the name of the repository
    :returns: a list of dictionaries, each representing a commit
    """
    filepath = pathlib.Path(f'data_collection/commit_data/{ledger}/{repo}_repo_commits.json')
    with open(filepath) as f:
        commits = json.load(f)  # sorted commits
    return commits


def write_contributions_per_entity_to_file(contributions_per_entity, mean_timestamps, filepath):
    """
    Produces a csv file with information about the contributions that each entity made over some timeframe.
    The entries are sorted so that the entities that controlled the most resources appear first.
    :param output_dir: pathlib.PosixPath object of the output directory where the produced csv file is written to.
    :param contributions_per_entity: a dictionary with entities as keys and lists as values, where each list represents the
        contributions made by each entity in each sample window
    :param mean_timestamps: a dictionary with sample window ids as keys and the mean timestamp of the commits in that
        sample window as values
    :param filepath: pathlib path to be used for the produced file.
    """
    with open(filepath, 'w', newline='') as f:
        sample_windows = mean_timestamps.keys()
        csv_writer = csv.writer(f)
        timestamps = list(mean_timestamps.values())
        if len(timestamps) > 1:
            # Write header if there is more than one sample window
            csv_writer.writerow(['Entity \\ Time'] + timestamps)
        else:
            csv_writer.writerow(['Entity', 'Contributions'])
        for entity, entity_commits in contributions_per_entity.items():
            entity_row = [entity]
            for sample_window in sample_windows:
                try:
                    entity_row.append(entity_commits[sample_window])
                except KeyError:
                    entity_row.append(0)
            csv_writer.writerow(entity_row)


def get_contributions_per_entity_from_file(filepath):
    """
    Retrieves information about the number of contributions that each entity made over some timeframe for some
    project.
    :param filepath: the path to the file with the relevant information. It can be either an absolute or a relative
    path in either a pathlib.PosixPath object or a string.
    :returns: a tuple of length 2 where the first item is a list of strings each representing the mean timestamp of a
    sample window and the second item is a dictionary with entities (keys) and a list of the number of contributions
    they made during each sample window (values)
    """
    contributions_per_entity = defaultdict(dict)
    with open(filepath, newline='') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader, None)
        sample_windows = header[1:]
        for row in csv_reader:
            entity = row[0]
            for idx, item in enumerate(row[1:]):
                contributions_per_entity[entity][idx] = int(item)
    return sample_windows, contributions_per_entity
