import asyncio
import sys
import time

import httpx
import uvicorn
from fastapi import FastAPI, Response


class CIDataManager:
    def __init__(self):
        self.ci_runs = []

    def add_run(self, run_data):
        self.ci_runs.append(run_data)
        print(f"Added run data: {run_data}")

    def get_runs(self):
        return self.ci_runs


app = FastAPI()
data_manager = CIDataManager()


@app.get("/")
def read_root():
    return Response("Server is running.")


@app.get("/runs")
def read_runs():
    runs = data_manager.get_runs()
    return {"total": len(runs), "data": runs}


async def get_current_commit(repo_path: str) -> str:
    """
    Gets the current commit hash of the repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        str: The current commit hash.
    """

    # execute a git command asynchronously to get current commit hash
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
    print(f"Sending request to {server_url} with data: {request_data}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                server_url,
                json=request_data,
            )
        print(f"Response for {step} step: {response.status_code}, {response.text}")

        if response.status_code != 200:
            return False
        response_data = response.json()
        return response_data.get("status") == "Success"

    except httpx.HTTPError as exc:
        print(f"HTTP error occurred: {exc}")
        return False
    except httpx.RemoteProtocolError:
        if step == "test":
            # server crash is expected during the 'test' step.
            print(
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
    new_commits = []

    while True:
        current_commit = await get_current_commit(repo_path)
        if current_commit != last_commit:
            new_commits.append(current_commit)
            last_commit = current_commit

        await asyncio.sleep(1)  # non-blocking sleep

        if new_commits and time.time() % 10 < 1:
            while new_commits:
                commit = new_commits.pop(0)
                run_result = {
                    "id": commit,
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

            print("CI run complete!")


async def main() -> None:
    repo_path = sys.argv[1]
    server_port = sys.argv[2].lstrip(":")
    server_url = f"http://localhost:{server_port}/step/trigger"

    if not server_url.startswith("http"):
        server_url = f"http://{server_url}"

    # start the CI service as a background task
    asyncio.create_task(ci_service(repo_path, server_url, data_manager))

    # configure and run the FastAPI app on a different port
    uvicorn_config = uvicorn.Config(app=app, host="0.0.0.0", port=9000, loop="asyncio")
    server = uvicorn.Server(config=uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
