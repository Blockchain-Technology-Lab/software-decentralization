import pathlib
import helper as hlp
from collections import defaultdict
import json


def group_users_by_email(commit_data, users_per_email=None):
    """
    Groups the users that contributed commits by their email.
    :param commit_data: a list of dictionaries, each containing the commit data
    :param users_per_email: an existing dictionary to add the counts to; a new one is created if not provided
    :returns: a dictionary with the emails as keys and a set of names as values
    """
    if users_per_email is None:
        users_per_email = defaultdict(lambda: defaultdict(int))
    for commit in commit_data:
        for contributor_type in ['author', 'committer']:
            name = commit[f'{contributor_type}_name']
            email = commit[f'{contributor_type}_email']
            if hlp.is_bot(name, email):
                continue
            users_per_email[email][name] += 1
    return users_per_email


def add_manual_entries(names):
    """
    Adds manual entries to the names dictionary, overriding any automatically assigned name.
    :param names: a dictionary with an email as key and a name as value
    :returns: an updated dictionary with the manual entries added
    """
    manual_entries = {
        'geffobscura@gmail.com': 'Jeffrey Wilcke',
        'obscuren@obscura.com': 'Jeffrey Wilcke'
    }
    names.update(manual_entries)
    return names


def assign_name_to_email(users_per_email):
    """
    Assigns a name to each email address. Chooses the name that has been associated with the email address the most
    times.
    :param users_per_email: a dictionary with the emails as keys and a set of names as values
    :returns: a dictionary with the emails as keys and a single name as value
    """
    email_to_name = {}
    for email, names in users_per_email.items():
        if len(names) > 1 and 'merge-script' in names:
            names.pop('merge-script')
        most_freq_name = max(names, key=names.get)
        email_to_name[email] = most_freq_name
    return email_to_name


def save_contributor_names_to_file(names, dir):
    """
    Saves the contributor names associated with email addresses to a file, ordered alphabetically by email.
    Before saving, commas are removed from the names, if present.
    :param names: a dictionary with an email as a key and a name as a value
    :param dir: the directory to save the file in
    """
    names = {email: name.replace(',', '') for email, name in names.items()}
    sorted_names = {email: name for email, name in sorted(names.items())}
    with open(dir / 'contributor_names.json', 'w') as f:
        json.dump(sorted_names, f, indent=4)


def get_contributor_names_from_file():
    """
    Reads the contributor names associated with email addresses from file.
    :returns: a dictionary with an email as a key and a name as a value
    """
    data_collection_path = pathlib.Path(__file__).parent / 'data_collection'
    contributor_names_dir = data_collection_path / 'contributor_names'

    with open(contributor_names_dir / 'contributor_names.json') as f:
        names = json.load(f)
    return names


def update_contributor_names(ledger_repos):
    """
    Regenerates the contributor name mapping file from the commit data of all repos.
    :param ledger_repos: dictionary with ledger names as keys and lists of repository names as values
    """
    data_collection_path = pathlib.Path(__file__).parent / 'data_collection'
    contributor_names_dir = data_collection_path / 'contributor_names'
    contributor_names_dir.mkdir(exist_ok=True, parents=True)

    users_per_email = defaultdict(lambda: defaultdict(int))
    for ledger, repos in ledger_repos.items():
        for repo in repos:
            commits = hlp.read_commit_data(ledger, repo)
            group_users_by_email(commits, users_per_email)
    names = assign_name_to_email(users_per_email)
    names = add_manual_entries(names)
    save_contributor_names_to_file(names, contributor_names_dir)
