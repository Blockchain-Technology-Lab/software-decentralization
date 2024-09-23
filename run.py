import logging
from collections import defaultdict
import helper as hlp
from metrics import *  # noqa
import pandas as pd
from plot import plot
from data_collection.collect_commit_data import fetch_data
from mapping import get_contributor_names_from_file


def aggregate(ledger, repo, commits_per_sample_window, contributor_type, contribution_type):
    output_dir = hlp.get_output_dir(output_type='data', contribution_type=contribution_type, contributor_type=contributor_type,
                                    commits_per_sample_window=commits_per_sample_window, data_type='contributions_per_entity', mkdir=True)
    logging.info(f'Processing {repo}...')

    contributor_names_by_email = get_contributor_names_from_file(repo)
    commits = hlp.read_commit_data(ledger, repo)

    # aggregate commits by the appropriate number of commits per sample window
    contributions_per_entity = defaultdict(dict)
    sample_window_timestamps = defaultdict(list)
    for i, commit in enumerate(reversed(commits)):
        sample_window_idx = i // commits_per_sample_window if commits_per_sample_window else 0
        sample_window_timestamps[sample_window_idx].append(commit[f'{contributor_type}_timestamp'])
        contributor_email = commit[f'{contributor_type}_email']
        contributor_name = contributor_names_by_email[contributor_email]
        contributions_per_entity[contributor_name][sample_window_idx] = contributions_per_entity[contributor_name].get(
            sample_window_idx, 0) + get_contribution_from_commit(commit, contribution_type)
    # remove last sample window if it has fewer observations than the rest
    if commits_per_sample_window and len(sample_window_timestamps[sample_window_idx]) < commits_per_sample_window:
        sample_window_timestamps.pop(sample_window_idx)
        for entity, contributions in contributions_per_entity.items():
            contributions.pop(sample_window_idx, None)
    mean_timestamps = {idx: pd.to_datetime(timestamps).mean().date() for idx, timestamps in
                       sample_window_timestamps.items()}
    filename = f'{repo}_contributions_per_entity.csv'
    hlp.write_contributions_per_entity_to_file(contributions_per_entity, mean_timestamps, output_dir / filename)


def get_contribution_from_commit(commit, contribution_type):
    if contribution_type == 'commits':
        return 1
    elif contribution_type == 'lines_added':
        return commit['lines_added']
    elif contribution_type == 'lines_deleted':
        return commit['lines_deleted']
    elif contribution_type == 'lines_changed':
        return commit['lines_added'] + commit['lines_deleted']
    elif contribution_type == 'merge_commits':
        return 1 if commit['message'].startswith('Merge') else 0
    else:
        raise ValueError(f'Invalid contribution type: {contribution_type}')


def run_metrics(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type):
    """
    Calculates metrics for the distribution in each sample window.
    Saves the results in a csv file in the 'output' directory.
    :param ledger_repos: dictionary with ledger names as keys and lists of repository names as values
    :param metrics: list of metric names
    :param commits_per_sample_window: int that represents the number of commits per sample window (or None)
    :param contributor_type: string with the type of entity to consider in the analysis (author or committer)
    :param contribution_type: string with the type of contribution to consider in the analysis (commits,
    merge_commits, lines_added, lines_deleted, or lines_changed)
    """
    logging.info('Calculating metrics...')
    contributions_per_entity_data_dir = hlp.get_output_dir(output_type='data', contribution_type=contribution_type,
                                                           contributor_type=contributor_type, commits_per_sample_window=commits_per_sample_window,
                                                           data_type='contributions_per_entity')
    metrics_data_dir = hlp.get_output_dir(output_type='data', contribution_type=contribution_type,
                                          contributor_type=contributor_type, commits_per_sample_window=commits_per_sample_window,
                                          data_type='metrics', mkdir=True)

    repos = [repo for repos in ledger_repos.values() for repo in repos]
    metric_dfs = {metric: pd.DataFrame() for metric in metrics}
    all_metrics_rows = []
    for repo in repos:
        sample_windows, contributions_per_entity = hlp.get_contributions_per_entity_from_file(
            contributions_per_entity_data_dir / f'{repo}_contributions_per_entity.csv')
        if len(sample_windows) > 1:
            sample_window_results = defaultdict(list)
            for metric in metrics:
                metric_repo_results = {}
                for sample_window_id in range(len(sample_windows)):
                    sample_contributions_per_entity = {}
                    for entity, contribution_values in contributions_per_entity.items():
                        sample_contributions_per_entity[entity] = contribution_values[sample_window_id]
                    # Remove entities with no commits in the sample window
                    sample_contributions_per_entity = {k: v for k, v in sample_contributions_per_entity.items() if
                                                       v > 0}
                    sorted_sample_commits = sorted(sample_contributions_per_entity.values(), reverse=True)
                    func = eval(f'compute_{metric}')
                    metric_repo_results[sample_window_id] = func(sorted_sample_commits)
                    sample_window_results[sample_window_id].append(metric_repo_results[sample_window_id])

                metric_df_repo = pd.DataFrame.from_dict(metric_repo_results, orient='index', columns=[repo])
                metric_dfs[metric] = metric_dfs[metric].join(metric_df_repo, how='outer')
            all_metrics_rows.extend([[repo, sample_windows[sample_window_id]] + results for sample_window_id, results in
                                     sample_window_results.items()])
    if all_metrics_rows:
        all_metrics_df = pd.DataFrame(all_metrics_rows, columns=['ledger', 'date'] + metrics)
        all_metrics_df.to_csv(metrics_data_dir / 'all_metrics.csv', index=False, date_format='%Y%m%d')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)

    ledger_repos = hlp.get_ledger_repos()
    refresh_data_flag = hlp.get_refresh_data_flag()
    fetch_data(repos=[(ledger, repo) for ledger in ledger_repos for repo in ledger_repos[ledger]],
               update_existing=refresh_data_flag)

    metrics = hlp.get_metrics()
    commits_per_sample_window_list = hlp.get_commits_per_sample_window_list()
    contributor_types = hlp.get_contributor_types()
    contribution_types = hlp.get_contribution_types()
    for contribution_type in contribution_types:
        logging.info(f'Processing by contribution type: {contribution_type}')
        for contributor_type in contributor_types:
            logging.info(f'Processing per contributor type: {contributor_type}')
            for commits_per_sample_window in commits_per_sample_window_list:
                logging.info(f'Processing with {commits_per_sample_window} commits per sample window')
                for ledger, repos in ledger_repos.items():
                    for repo in repos:
                        aggregate(ledger, repo, commits_per_sample_window, contributor_type, contribution_type)
                run_metrics(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type)
                plot(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type)
