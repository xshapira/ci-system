import subprocess
import time
from pathlib import Path

import requests


def get_current_commit(repo_path):
    """
    Gets the current commit hash of the repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        str: The current commit hash.
    """
    return (
        subprocess.check_output(["git", "-C", repo_path, "rev-parse", "HEAD"])
        .strip()
        .decode("utf-8")
    )


def send_requests(commit, repo_path, server_url):
    """
    Sends POST requests to the server for linting, building, and testing.

    Args:
        commit (str): The commit hash.
        repo_path (str): The path to the repository.
        server_url (str): The URL of the server.
    """
    requests.post(
        server_url,
        json={"commit_hash": commit, "step_name": "lint", "repo_path": repo_path},
    )
    requests.post(
        server_url,
        json={"commit_hash": commit, "step_name": "build", "repo_path": repo_path},
    )
    requests.post(
        server_url,
        json={"commit_hash": commit, "step_name": "test", "repo_path": repo_path},
    )


def ci_service(repo_path, server_url):
    """
    Continuously check for new commits and send requests to the server.

    Args:
        repo_path (str): The path to the repository.
        server_url (str): The URL of the server.
    """
    last_commit = get_current_commit(repo_path)
    new_commits = []

    while True:
        current_commit = get_current_commit(repo_path)
        if current_commit != last_commit:
            new_commits.append(current_commit)
            last_commit = current_commit

        time.sleep(1)

        if new_commits and time.time() % 10 < 1:
            for commit in new_commits:
                send_requests(commit, repo_path, server_url)
                new_commits.remove(commit)


def main() -> None:
    # get absolute path
    repo_path = str(Path.cwd().resolve())
    server_url = "http://localhost:8080"

    ci_service(repo_path, server_url)


if __name__ == "__main__":
    main()
