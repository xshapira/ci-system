import asyncio
import subprocess
import sys
import time

import requests


class CIDataManager:
    def __init__(self):
        self.ci_runs = []

    def add_run(self, run_data):
        self.ci_runs.append(run_data)

    def get_runs(self):
        return self.ci_runs


def get_current_commit(repo_path: str) -> str:
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


def run_step(
    commit: str,
    repo_path: str,
    server_url: str,
    step: str,
) -> bool:
    """
    Runs a CI pipeline step and checks if it succeeded.

    Sends a POST request to the server to run a CI step. Checks the
    response status code to see if the step executed successfully.

    Args:
        commit (str): The commit hash.
        repo_path (str): The path to the repository.
        server_url (str): The URL of the server.

    Returns:
        bool: True if the step executed successfully, False otherwise.
    """
    response = requests.post(
        server_url,
        json={"commit_hash": commit, "step_name": step, "repo_path": repo_path},
    )
    if response.status_code != 200:
        return False
    response_data = response.json()

    return response_data.get("status") == "success"


async def ci_service(
    repo_path: str,
    server_url: str,
    data_manager: CIDataManager,
) -> None:
    """
    Continuously check for new commits and send requests to the server.

    Args:
        repo_path (str): The path to the repository.
        server_url (str): The URL of the server.
    """
    last_commit = await get_current_commit(repo_path)
    new_commits = []

    while True:
        current_commit = await get_current_commit(repo_path)
        if current_commit != last_commit:
            new_commits.append(current_commit)
            last_commit = current_commit

        await asyncio.sleep(1)  # non-blocking sleep

        if new_commits and time.time() % 10 < 1:
            for commit in new_commits:
                run_result = {
                    "commit_hash": commit,
                    "status": "success",
                }

                passed = await run_step(commit, repo_path, server_url, "lint")
                if not passed:
                    print(f"Lint failed for commit {commit}")
                    run_result["status"] = "failure"
                    data_manager.add_run(run_result)
                    continue

                passed = await run_step(commit, repo_path, server_url, "build")
                if not passed:
                    print(f"Build failed for commit {commit}")
                    run_result["status"] = "failure"
                    data_manager.add_run(run_result)
                    continue

                await run_step(commit, repo_path, server_url, "test")
                data_manager.add_run(run_result)

                new_commits.remove(commit)
            print("CI run complete!")


def main() -> None:
    repo_path = sys.argv[1]
    server_port = sys.argv[2].lstrip(":")
    server_url = f"http://localhost:{server_port}"

    if not server_url.startswith("http"):
        server_url = f"http://{server_url}"

    ci_service(repo_path, server_url)


if __name__ == "__main__":
    main()
