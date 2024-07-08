import json
import logging
from collections import defaultdict
import helper as hlp
import pathlib
from metrics import *  # noqa
import pandas as pd
from plot import plot


def aggregate(ledger_repos, granularity, entity_type, weight_type):
    output_dir = pathlib.Path(f'output/by_{weight_type}/per_{entity_type}/commits_per_entity_{granularity}')
    output_dir.mkdir(parents=True, exist_ok=True)
    for ledger, repos in ledger_repos.items():
        for repo in repos:
            logging.info(f'Processing {repo}...')
            with open(f'data_collection/commit_data/{ledger}/{repo}_repo_commits.json') as f:
                commits = json.load(f)  # sorted commits

            # aggregate commits by granularity
            commits_per_entity = defaultdict(dict)
            sample_windows = set()
            for i, commit in enumerate(commits):
                sample_window_idx = i // granularity
                sample_windows.add(sample_window_idx)
                committer = commit['author_name']
                commits_per_entity[committer][sample_window_idx] = commits_per_entity[committer].get(sample_window_idx, 0) + get_weight_from_commit(commit, weight_type)
            hlp.write_commits_per_entity_to_file(commits_per_entity, list(sample_windows), output_dir / f'{ledger}_{repo}_commits_per_entity.csv')


def get_weight_from_commit(commit, weight_type):
    if weight_type == 'number_of_commits':
        return 1
    elif weight_type == 'lines_added':
        return commit['lines_added']
    elif weight_type == 'lines_deleted':
        return commit['lines_deleted']
    elif weight_type == 'total_lines':
        return commit['lines_added'] + commit['lines_deleted']
    else:
        raise ValueError(f'Invalid weight type: {weight_type}')


def run_metrics(ledger_repos, metrics, granularity, entity_type, weight_type):
    logging.info('Calculating metrics...')
    output_dir = pathlib.Path(f'output/by_{weight_type}/per_{entity_type}')
    commits_per_entity_dir = output_dir / f'commits_per_entity_{granularity}'
    metrics_dir = output_dir / 'metrics'
    metrics_dir.mkdir(parents=True, exist_ok=True)

    repos = [f'{ledger}_{repo}' for ledger, repos in ledger_repos.items() for repo in repos]
    metric_dfs = {metric: pd.DataFrame() for metric in metrics}
    for repo in repos:
        sample_windows, commits_per_entity = hlp.get_blocks_per_entity_from_file(commits_per_entity_dir / f'{repo}_commits_per_entity.csv')
        for metric in metrics:
            metric_repo_results = {}
            for sample_idx in sample_windows:
                sample_commits_per_entity = {}
                for entity, commit_values in commits_per_entity.items():
                    sample_commits_per_entity[entity] = commit_values[sample_idx]
                # Remove entities with no commits in the sample window
                sample_commits_per_entity = {k: v for k, v in sample_commits_per_entity.items() if v > 0}
                sorted_sample_commits = sorted(sample_commits_per_entity.values(), reverse=True)
                func = eval(f'compute_{metric}')
                metric_repo_results[sample_idx] = func(sorted_sample_commits)
            metric_df_repo = pd.DataFrame.from_dict(metric_repo_results, orient='index', columns=[repo])
            metric_dfs[metric] = metric_dfs[metric].join(metric_df_repo, how='outer')
    for metric in metrics:
        metric_dfs[metric].to_csv(metrics_dir / f'{metric}.csv', index_label='sample')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
    ledger_repos = hlp.get_ledger_repos()
    metrics = hlp.get_metrics()
    granularity = hlp.get_granularity()
    entity_types = hlp.get_entity_types()
    weight_types = hlp.get_weight_types()
    for weight_type in weight_types:
        logging.info(f'Processing by weight type: {weight_type}')
        for entity_type in entity_types:
            logging.info(f'Processing per entity type: {entity_type}')
            aggregate(ledger_repos, granularity, entity_type, weight_type)
            run_metrics(ledger_repos, metrics, granularity, entity_type, weight_type)
            plot(ledger_repos, metrics, granularity, entity_type, weight_type)
