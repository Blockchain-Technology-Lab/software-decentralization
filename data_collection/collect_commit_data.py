import json
import logging
import pathlib
import git
from datetime import datetime


def get_commit_data(git_repo, branch, filepath):
    try:
        with open(filepath) as f:
            existing_commits = json.load(f)
    except FileNotFoundError:
        existing_commits = []
    existing_commits_num = len(existing_commits)

    total_commits_num = int(git_repo.git.rev_list('--count', branch))
    new_commits_num = total_commits_num - existing_commits_num

    commits_list = []
    if new_commits_num > 0:
        for commit in git_repo.iter_commits(branch, max_count=new_commits_num):
            commit_dict = {
                'hash': commit.hexsha,
                'author_name': commit.author.name,
                'author_email': commit.author.email,
                'author_timestamp': str(datetime.fromtimestamp(commit.authored_date)),
                'committer_name': commit.committer.name,
                'committer_email': commit.committer.email,
                'committer_timestamp': str(datetime.fromtimestamp(commit.committed_date)),
                'message': commit.message,
                'lines_added': commit.stats.total['insertions'],
                'lines_deleted': commit.stats.total['deletions']
            }
            commits_list.append(commit_dict)

    commits_list.extend(existing_commits)
    assert len(commits_list) - existing_commits_num == new_commits_num

    if new_commits_num > 0:
        with open(filepath, 'w') as f:
            json.dump(commits_list, f, indent=4)

    logging.info(f'Fetched {new_commits_num} new commits. Total commits saved: {len(commits_list)}')


def fetch_data(repos, update_existing):
    """
    Fetches commit data for the specified repositories.
    :param repos: either "all" (which corresponds to all repositories in the repo_info.json file) or a
    list of tuples in the form (ledger, repo_name)
    :param update_existing: boolean that indicates whether to update commit data or not for repositories that have
    already been cloned
    """
    data_collection_path = pathlib.Path(__file__).parent

    with open(data_collection_path / 'repo_info.json') as f:
        repo_info = json.load(f)
    if repos == 'all':
        repos = [(ledger, repo) for ledger in repo_info for repo in repo_info[ledger]]

    for ledger, repo_name in repos:
        repo_owner = repo_info[ledger][repo_name]['owner']
        repo_branch = repo_info[ledger][repo_name]['branch']

        local_repo_dir = data_collection_path / f'repos/{ledger}/{repo_name}'
        local_repo_dir.mkdir(exist_ok=True, parents=True)
        commits_needed = False
        try:
            git_repo = git.Repo(local_repo_dir)
            if update_existing:
                logging.info(f'Fetching latest commits from {repo_name} ({ledger}) repository...')
                git_repo.remotes.origin.pull()
                commits_needed = True
        except git.exc.InvalidGitRepositoryError:
            logging.info(f'Cloning {repo_name} ({ledger}) repository and fetching all commits...')
            repo_url = f'https://github.com/{repo_owner}/{repo_name}.git'
            git_repo = git.Repo.clone_from(repo_url, local_repo_dir)
            commits_needed = True

        if commits_needed:
            commit_data_dir = data_collection_path / 'commit_data' / ledger
            commit_data_dir.mkdir(exist_ok=True, parents=True)
            repo_commits_filepath = data_collection_path / f'commit_data/{ledger}/{repo_name}_repo_commits.json'
            get_commit_data(git_repo, repo_branch, repo_commits_filepath)


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
    fetch_data(repos='all', update_existing=True)
