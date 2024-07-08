import csv
from collections import defaultdict
from yaml import safe_load


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
    return config['repositories']


def get_metrics():
    """
    Retrieves the list of metrics that are to be calculated.
    :returns: a list of strings, each corresponding to a metric
    """
    config = get_config_data()
    return config['metrics']


def get_granularity():
    """
    Retrieves the granularity that will be used for the analysis.
    :returns: a number that corresponds to the granularity (number of commits per sample window) that will be used.
    """
    config = get_config_data()
    return config['granularity']


def get_entity_types():
    """
    Retrieves the list of entity types that will be considered in the analysis.
    :returns: a list of strings, each corresponding to an entity type
    """
    config = get_config_data()
    return config['entity_types']


def write_commits_per_entity_to_file(commits_per_entity, sample_windows, filepath):
    """
    Produces a csv file with information about the resources (blocks) that each entity controlled over some timeframe.
    The entries are sorted so that the entities that controlled the most resources appear first.
    :param output_dir: pathlib.PosixPath object of the output directory where the produced csv file is written to.
    :param commits_per_entity: a dictionary with entities as keys and lists as values, where each list represents the
        number of commits authored by the entity in each sample window
    :param sample_windows: a list of strings corresponding to the sample windows that were analyzed
    :param filepath: pathlib path to be used for the produced file.
    """
    with open(filepath, 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['Entity \\ Time period'] + sample_windows)  # write header
        for entity, commits_per_chunk in commits_per_entity.items():
            entity_row = [entity]
            for chunk in sample_windows:
                try:
                    entity_row.append(commits_per_chunk[chunk])
                except KeyError:
                    entity_row.append(0)
            csv_writer.writerow(entity_row)


def get_blocks_per_entity_from_file(filepath):
    """
    Retrieves information about the number of blocks that each entity produced over some timeframe for some project.
    :param filepath: the path to the file with the relevant information. It can be either an absolute or a relative
    path in either a pathlib.PosixPath object or a string.
    :returns: a tuple of length 2 where the first item is a list of sample window ids (strings) and the second item is a
    dictionary with entities (keys) and a list of the number of commits they contributed during each sample window (values)
    """
    commits_per_entity = defaultdict(dict)
    with open(filepath, newline='') as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader, None)
        sample_windows = [int(i) for i in header[1:]]
        for row in csv_reader:
            entity = row[0]
            for idx, item in enumerate(row[1:]):
                commits_per_entity[entity][sample_windows[idx]] = int(item)
    return sample_windows, commits_per_entity
