import json
import logging
from collections import defaultdict
import helper as hlp
from metrics import *  # noqa
import pandas as pd
from plot import plot


def aggregate(ledger, repo, granularity, entity_type, weight_type):
    output_dir = hlp.get_output_dir(output_type='data', weight_type=weight_type, entity_type=entity_type,
                                    granularity=granularity, data_type='commits_per_entity', mkdir=True)
    logging.info(f'Processing {repo}...')
    commits = hlp.read_commit_data(ledger, repo)

    # aggregate commits by granularity
    commits_per_entity = defaultdict(dict)
    sample_window_timestamps = defaultdict(list)
    for i, commit in enumerate(reversed(commits)):
        sample_window_idx = i // granularity if granularity else 0
        sample_window_timestamps[sample_window_idx].append(commit[f'{entity_type}_timestamp'])
        entity = commit[f'{entity_type}_name']
        commits_per_entity[entity][sample_window_idx] = commits_per_entity[entity].get(sample_window_idx,
                                                                                       0) + get_weight_from_commit(
            commit, weight_type)
    mean_timestamps = {idx: pd.to_datetime(timestamps).mean().date() for idx, timestamps in
                       sample_window_timestamps.items()}
    filename = f'{repo}_commits_per_entity.csv'
    hlp.write_commits_per_entity_to_file(commits_per_entity, mean_timestamps, output_dir / filename)


def get_weight_from_commit(commit, weight_type):
    if weight_type == 'number_of_commits':
        return 1
    elif weight_type == 'lines_added':
        return commit['lines_added']
    elif weight_type == 'lines_deleted':
        return commit['lines_deleted']
    elif weight_type == 'lines_changed':
        return commit['lines_added'] + commit['lines_deleted']
    elif weight_type == 'number_of_merge_commits':
        return 1 if commit['message'].startswith('Merge') else 0
    else:
        raise ValueError(f'Invalid weight type: {weight_type}')


def run_metrics(ledger_repos, metrics, granularity, entity_type, weight_type):
    """
    Calculates metrics for the distribution in each sample window.
    Saves the results in a csv file in the 'output' directory.
    :param ledger_repos: dictionary with ledger names as keys and lists of repository names as values
    :param metrics: list of metric names
    :param granularity: int that represents the number of commits per sample window (or None)
    :param entity_type: string with the type of entity to consider in the analysis (author or committer)
    :param weight_type: string with the type of weight to consider in the analysis (number_of_commits, lines_added,
    lines_deleted, or lines_changed)
    """
    logging.info('Calculating metrics...')
    commits_per_entity_data_dir = hlp.get_output_dir(output_type='data', weight_type=weight_type,
                                                     entity_type=entity_type, granularity=granularity,
                                                     data_type='commits_per_entity')
    metrics_data_dir = hlp.get_output_dir(output_type='data', weight_type=weight_type, entity_type=entity_type,
                                          granularity=granularity, data_type='metrics', mkdir=True)

    repos = [repo for repos in ledger_repos.values() for repo in repos]
    metric_dfs = {metric: pd.DataFrame() for metric in metrics}
    all_metrics_rows = []
    for repo in repos:
        sample_windows, commits_per_entity = hlp.get_blocks_per_entity_from_file(
            commits_per_entity_data_dir / f'{repo}_commits_per_entity.csv')
        if len(sample_windows) > 1:
            sample_window_results = defaultdict(list)
            for metric in metrics:
                metric_repo_results = {}
                for sample_window_id in range(len(sample_windows)):
                    sample_commits_per_entity = {}
                    for entity, commit_values in commits_per_entity.items():
                        sample_commits_per_entity[entity] = commit_values[sample_window_id]
                    # Remove entities with no commits in the sample window
                    sample_commits_per_entity = {k: v for k, v in sample_commits_per_entity.items() if v > 0}
                    sorted_sample_commits = sorted(sample_commits_per_entity.values(), reverse=True)
                    func = eval(f'compute_{metric}')
                    metric_repo_results[sample_window_id] = func(sorted_sample_commits)
                    sample_window_results[sample_window_id].append(metric_repo_results[sample_window_id])

                metric_df_repo = pd.DataFrame.from_dict(metric_repo_results, orient='index', columns=[repo])
                metric_dfs[metric] = metric_dfs[metric].join(metric_df_repo, how='outer')
            all_metrics_rows.extend(
                [[repo, sample_windows[sample_window_id]] + results for sample_window_id, results in
                 sample_window_results.items()])
    if all_metrics_rows:
        all_metrics_df = pd.DataFrame(all_metrics_rows, columns=['ledger', 'date'] + metrics)
        all_metrics_df.to_csv(metrics_data_dir / 'all_metrics.csv', index=False, date_format='%Y%m%d')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
    ledger_repos = hlp.get_ledger_repos()
    metrics = hlp.get_metrics()
    granularities = hlp.get_granularities()
    entity_types = hlp.get_entity_types()
    weight_types = hlp.get_weight_types()
    for weight_type in weight_types:
        logging.info(f'Processing by weight type: {weight_type}')
        for entity_type in entity_types:
            logging.info(f'Processing per entity type: {entity_type}')
            for granularity in granularities:
                logging.info(f'Processing with granularity (number of commits per sample window): {granularity}')
                for ledger, repos in ledger_repos.items():
                    for repo in repos:
                        aggregate(ledger, repo, granularity, entity_type, weight_type)
                run_metrics(ledger_repos, metrics, granularity, entity_type,
                            weight_type)
                plot(ledger_repos, metrics, granularity, entity_type, weight_type)
