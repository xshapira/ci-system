import asyncio
import functools
import time
from collections import deque

import httpx

from logger import setup_logger

log = setup_logger(__name__)


class CIDataManager:
    def __init__(self):
        self.ci_runs = []

    def add_run(self, run_data):
        self.ci_runs.append(run_data)
        log.info(f"Added run data: {run_data}")

    def get_runs(self):
        return self.ci_runs

    @classmethod
    @functools.cache
    def get_instance(cls):
        return cls()


async def get_current_commit(repo_path: str) -> str:
    """
    Gets the current commit hash of the repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        str: The current commit hash.
    """

    # execute git command asynchronously to get current commit hash
    process = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        repo_path,
        "rev-parse",
        "HEAD",
        stdout=asyncio.subprocess.PIPE,  # capture only standard output
    )
    stdout, _ = await process.communicate()
    # return None if the command fails
    # otherwise decode and return the commit hash
    return None if process.returncode != 0 else stdout.decode("utf-8").strip()


async def run_step(
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
    request_data = {
        "commit_hash": commit,
        "step_name": step,
        "repo_path": repo_path,
    }
    log.info(f"Sending request to {server_url} with data: {request_data}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                server_url,
                json=request_data,
            )
        log.info(f"Response for {step} step: {response.status_code}, {response.text}")

        if response.status_code != 200:
            return False
        response_data = response.json()
        return response_data.get("status") == "Success"

    except httpx.HTTPError as exc:
        log.info(f"HTTP error occurred: {exc}")
        return False
    except httpx.RemoteProtocolError:
        if step == "test":
            # server crash is expected during the 'test' step.
            log.info(
                "Server crash expected during the 'test' step. ",
                f"Commit: {commit}",
            )
            return False


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
    new_commits = deque()

    while True:
        current_commit = await get_current_commit(repo_path)
        if current_commit != last_commit:
            new_commits.append(current_commit)
            last_commit = current_commit

        await asyncio.sleep(1)

        if new_commits and time.time() % 10 < 1:
            while new_commits:
                commit = new_commits.popleft()
                run_result = {
                    "id": commit,
                    "status": "success",
                }
                for step in ["lint", "build", "test"]:
                    passed = await run_step(commit, repo_path, server_url, step)
                    if not passed:
                        log.info(f"{step.capitalize()} failed for commit {commit}")
                        failed_steps = run_result.get("failed_steps", [])
                        failed_steps.append(step)
                        # update run_result with modified failed_steps list
                        run_result["failed_steps"] = failed_steps
                        run_result["status"] = "failure"

                data_manager.add_run(run_result)
            log.info("CI run complete!")
