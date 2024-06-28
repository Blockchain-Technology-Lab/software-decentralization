import json
import logging
import pathlib
import git  # pip package gitpython
from datetime import datetime


def collect_commit_data(repo_name, repo_dir, branch, filepath):
    logging.info(f'Collecting {repo_name} commit data...')
    try:
        with open(filepath) as f:
            existing_commits = json.load(f)
    except FileNotFoundError:
        existing_commits = []
    existing_commits_num = len(existing_commits)

    repo = git.Repo(repo_dir)
    total_commits_num = int(repo.git.rev_list('--count', branch))
    new_commits_num = total_commits_num - existing_commits_num

    commits_list = []
    if new_commits_num > 0:
        for commit in repo.iter_commits(branch, max_count=new_commits_num):
            commit_dict = {
                'hash': commit.hexsha,
                'author_name': commit.author.name,
                'author_email': commit.author.email,
                'timestamp_authored': str(datetime.fromtimestamp(commit.authored_date)),
                'committer_name': commit.committer.name,
                'committer_email': commit.committer.email,
                'timestamp_committed': str(datetime.fromtimestamp(commit.committed_date)),
                'message': commit.message,
                'lines_added': commit.stats.total['insertions'],
                'lines_deleted': commit.stats.total['deletions']
            }
            commits_list.append(commit_dict)

        commits_list.extend(existing_commits)
        assert len(commits_list) - existing_commits_num == new_commits_num

        with open(filepath, 'w') as f:
            json.dump(commits_list, f, indent=4)

    logging.info(f'Collected {new_commits_num} new commits. Total commits saved: {len(commits_list)}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    data_collection_path = pathlib.Path(__file__).parent

    with open(data_collection_path / 'repo_info.json') as f:
        repo_info = json.load(f)

    for ledger, ledger_repos in repo_info.items():
        for repo in ledger_repos:
            repo_name = repo['name']
            local_repo_dir = data_collection_path / f'repos/{ledger}/{repo_name}'
            local_repo_dir.mkdir(exist_ok=True, parents=True)
            repo_url = f'https://github.com/{repo["owner"]}/{repo_name}.git'

            logging.info(f'Cloning {repo_name} ({ledger}) repository (or pulling latest changes if repository already '
                         f'cloned)...')
            try:
                git.Repo.clone_from(repo_url, local_repo_dir)
            except git.exc.GitCommandError:
                git_repo = git.Repo(local_repo_dir)
                git_repo.remotes.origin.pull()

            commit_data_dir = data_collection_path / 'commit_data' / ledger
            commit_data_dir.mkdir(exist_ok=True, parents=True)
            repo_commits_filepath = data_collection_path / f'commit_data/{ledger}/{repo_name}_repo_commits.json'
            collect_commit_data(repo_name, local_repo_dir, repo['branch'], repo_commits_filepath)
