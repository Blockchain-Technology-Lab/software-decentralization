import logging
from collections import defaultdict
import helper as hlp
from metrics import *  # noqa
import pandas as pd
from plot import plot
from data_collection.collect_commit_data import fetch_data
from mapping import get_contributor_names_from_file, update_contributor_names


def aggregate(ledger, repos, commits_per_sample_window, contributor_type, contribution_type):
    output_dir = hlp.get_output_dir(ledger, output_type='data', data_type='contributions_per_entity',
                                    contribution_type=contribution_type, contributor_type=contributor_type,
                                    commits_per_sample_window=commits_per_sample_window, mkdir=True)

    contributor_names_by_email = get_contributor_names_from_file()
    # merge the commits of all repos of the ledger into a single chronological history, excluding bot commits
    commits = [commit for repo in repos for commit in hlp.read_commit_data(ledger, repo)]
    commits = [commit for commit in commits
              if not hlp.is_bot(commit[f'{contributor_type}_name'], commit[f'{contributor_type}_email'])]
    commits.sort(key=lambda commit: commit[f'{contributor_type}_timestamp'])

    # aggregate commits by the appropriate number of commits per sample window
    contributions_per_entity = defaultdict(dict)
    sample_window_timestamps = defaultdict(list)
    for i, commit in enumerate(commits):
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
    hlp.write_contributions_per_entity_to_file(contributions_per_entity, mean_timestamps, output_dir / 'contributions_per_entity.csv')


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
    Calculates metrics for the distribution in each sample window, for each ledger.
    Saves the results in a metrics.csv file under each ledger's own output directory.
    :param ledger_repos: dictionary with ledger names as keys and lists of repository names as values
    :param metrics: list of metric names
    :param commits_per_sample_window: int that represents the number of commits per sample window (or None)
    :param contributor_type: string with the type of entity to consider in the analysis (author or committer)
    :param contribution_type: string with the type of contribution to consider in the analysis (commits,
    merge_commits, lines_added, lines_deleted, or lines_changed)
    """
    logging.info('Calculating metrics...')
    for ledger in ledger_repos:
        contributions_per_entity_data_dir = hlp.get_output_dir(ledger, output_type='data', data_type='contributions_per_entity',
                                                                contribution_type=contribution_type,
                                                                contributor_type=contributor_type,
                                                                commits_per_sample_window=commits_per_sample_window)
        sample_windows, contributions_per_entity = hlp.get_contributions_per_entity_from_file(
            contributions_per_entity_data_dir / 'contributions_per_entity.csv')
        if len(sample_windows) <= 1:
            continue

        metrics_rows = []
        for sample_window_id in range(len(sample_windows)):
            sample_contributions_per_entity = {}
            for entity, contribution_values in contributions_per_entity.items():
                sample_contributions_per_entity[entity] = contribution_values[sample_window_id]
            # Remove entities with no commits in the sample window
            sample_contributions_per_entity = {k: v for k, v in sample_contributions_per_entity.items() if v > 0}
            sorted_sample_commits = sorted(sample_contributions_per_entity.values(), reverse=True)
            row = [ledger, sample_windows[sample_window_id]]
            for metric in metrics:
                func = eval(f'compute_{metric}')
                row.append(func(sorted_sample_commits))
            metrics_rows.append(row)

        metrics_data_dir = hlp.get_output_dir(ledger, output_type='data', data_type='metrics',
                                              contribution_type=contribution_type,
                                              contributor_type=contributor_type,
                                              commits_per_sample_window=commits_per_sample_window, mkdir=True)
        metrics_df = pd.DataFrame(metrics_rows, columns=['ledger', 'date'] + metrics)
        metrics_df.to_csv(metrics_data_dir / 'metrics.csv', index=False, date_format='%Y%m%d')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)

    ledger_repos = hlp.get_ledger_repos()
    refresh_data_flag = hlp.get_refresh_data_flag()
    fetch_data(repos=[(ledger, repo) for ledger in ledger_repos for repo in ledger_repos[ledger]],
               update_existing=refresh_data_flag)
    update_contributor_names(ledger_repos)

    metrics = hlp.get_metrics()
    plot_flag = hlp.get_plot_flag()
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
                    aggregate(ledger, repos, commits_per_sample_window, contributor_type, contribution_type)
                run_metrics(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type)
                if plot_flag:
                    plot(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type)
