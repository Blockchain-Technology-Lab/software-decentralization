import json
import logging
from collections import defaultdict
import helper as hlp
import pathlib
from metrics import *  # noqa
import pandas as pd


def aggregate(ledger_repos):
    granularity = hlp.get_granularity()
    output_dir = pathlib.Path(f'output/commits_per_entity_{granularity}')
    for ledger, repos in ledger_repos.items():
        output_dir.mkdir(parents=True, exist_ok=True)
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
                commits_per_entity[committer][sample_window_idx] = commits_per_entity[committer].get(sample_window_idx, 0) + 1
            hlp.write_commits_per_entity_to_file(commits_per_entity, list(sample_windows), output_dir / f'{ledger}_{repo}_commits_per_entity.csv')


def run_metrics(ledger_repos):
    logging.info('Calculating metrics...')
    granularity = hlp.get_granularity()
    output_dir = pathlib.Path(f'output')
    commits_per_entity_dir = output_dir / f'commits_per_entity_{granularity}'
    metrics_dir = output_dir / 'metrics'
    metrics_dir.mkdir(parents=True, exist_ok=True)

    metrics = hlp.get_metrics()
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
    aggregate(ledger_repos)
    run_metrics(ledger_repos)
