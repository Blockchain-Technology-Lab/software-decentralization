import json
from collections import Counter

import requests
import csv
import logging

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)


def read_access_token_from_file():
    """
    Reads the GitHub access token from a file.
    Make sure to add your token to the file 'gh_access_token.txt' under the same directory.
    :returns: string that corresponds to a GitHub access token.
    :raises: FileNotFoundError if the file is not found.
    """
    try:
        with open('data_collection/gh_access_token.txt', 'r') as f:
            token = f.read().strip()
        if token == '':
            raise ValueError(
                'No GitHub access token found. Make sure to add your GitHub access token in the "gh_access_token.txt" file.')
        return token
    except FileNotFoundError:
        raise FileNotFoundError(
            'File not found. Make sure to add your GitHub access token to a file called "gh_access_token.txt".')


def collect_contribution_data(repo_info):
    """
    Collects contribution data from the GitHub API and saves it to csv files.
    :param repo_info: dictionary where each key corresponds to a ledger and each value is a tuple with the owner (string) and the name (string) of the ledger's repository.
    """
    token = read_access_token_from_file()
    headers = {'Authorization': f'token {token}'}

    base_url = 'https://api.github.com/repos'

    for ledger, (owner, repo_name) in repo_info.items():
        logging.info(f'Collecting {ledger} contribution data...')
        contributors = []
        max_page_no = 1000
        for i in range(1, max_page_no + 1):
            url = f"{base_url}/{owner}/{repo_name}/contributors?per_page=100&page={i}"
            page_contributors = requests.get(url, headers=headers).json()
            if page_contributors.get('status', 0) == '403':
                logging.info('API rate limit exceeded. Contributor data may be incomplete.')
                break
            if len(page_contributors) > 0:
                contributors.extend(page_contributors)
            else:
                break
        contribution_distr = {contributor['login']: contributor['contributions'] for contributor in contributors}
        with open(f'data_collection/{ledger}_contributors.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['contributor', 'contributions'])
            writer.writerows(contribution_distr.items())


def collect_commit_data(repo_info):
    token = read_access_token_from_file()
    headers = {'Authorization': f'token {token}'}

    base_url = 'https://api.github.com/repos'
    for ledger, (owner, repo_name) in repo_info.items():
        logging.info(f'Collecting {ledger} commit data...')
        commits = []
        max_page_no = 1000
        for page_no in range(1, max_page_no + 1):
            url = f"{base_url}/{owner}/{repo_name}/commits?per_page=100&page={page_no}"
            page_commits = requests.get(url, headers=headers).json()
            if page_commits.get('status', 0) == '403':
                logging.info('API rate limit exceeded. Commit data may be incomplete.')
                break
            if len(page_commits) > 0:
                commits.extend(page_commits)
            else:
                break
        if page_no == max_page_no:
            logging.info('Maximum page number reached. Commit data may be incomplete.')
        commits_list = []
        for commit in commits:
            commit_url = commit['url']
            commit_data = requests.get(commit_url, headers=headers).json()
            if commit_data.get('status', 0) == '403':
                logging.info('API rate limit exceeded. Commit data may be incomplete.')
                break
            try:
                author_login = commit_data['author']['login']
            except (TypeError, KeyError):
                author_login = None
            try:
                committer_login = commit_data['committer']['login']
            except (TypeError, KeyError):
                committer_login = None
            commit_dict = {
                'url': commit_url,
                'author': {
                    'login': author_login,
                    'name': commit_data['commit']['author']['name'],
                    'email': commit_data['commit']['author']['email']
                },
                'committer': {
                    'login': committer_login,
                    'name': commit_data['commit']['committer']['name'],
                    'email': commit_data['commit']['committer']['email']
                },
                'timestamp_authored': commit_data['commit']['author']['date'],
                'timestamp_committed': commit_data['commit']['committer']['date'],
                'message': commit_data['commit']['message'],
                'loc_added': commit_data['stats']['additions'],
                'loc_deleted': commit_data['stats']['deletions']
            }
            commits_list.append(commit_dict)
        with open(f'data_collection/{ledger}_commits.json', 'w') as f:
            json.dump(commits_list, f, indent=4)


if __name__ == '__main__':
    repo_info = {
        'bitcoin': ('bitcoin', 'bitcoin'),
        'ethereum': ('ethereum', 'go-ethereum'),
        'cardano': ('input-output-hk', 'cardano-node')
    }
    # collect_contribution_data(repo_info)
    collect_commit_data(repo_info)
