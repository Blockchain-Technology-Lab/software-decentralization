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
            raise ValueError('No GitHub access token found. Make sure to add your GitHub access token in the "gh_access_token.txt" file.')
        return token
    except FileNotFoundError:
        raise FileNotFoundError('File not found. Make sure to add your GitHub access token to a file called "gh_access_token.txt".')
    

def collect_data(repo_info):
    """
    Collects contribution data from the GitHub API and saves it to csv files.
    :param repo_info: dictionary where each key corresponds to a ledger and each value is a tuple with the owner (string) and the name (string) of the ledger's repository.
    """
    token = read_access_token_from_file()
    headers = {'Authorization': f'token {token}'}

    base_url = 'https://api.github.com/repos'

    for ledger, (owner, repo_name) in repo_info.items():
        logging.info(f'Collecting {ledger} data...')
        contributors = []
        max_page_no = 1000
        for i in range(1, max_page_no + 1):
            url = f"{base_url}/{owner}/{repo_name}/contributors?per_page=100&page={i}"
            page_contributors = requests.get(url, headers=headers).json()
            if len(page_contributors) > 0:
                contributors.extend(page_contributors)
            else:
                break
        contribution_distr = {contributor['login']: contributor['contributions'] for contributor in contributors}
        with open(f'data_collection/{ledger}_contributors.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['contributor', 'contributions'])
            writer.writerows(contribution_distr.items())

if __name__ == '__main__':
    repo_info = {
        'bitcoin': ('bitcoin', 'bitcoin')
    }
    collect_data(repo_info)
