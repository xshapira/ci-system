# Sorry for the mess, I left the code in a hurry! I'm sure you can figure it
# out. Good luck!
import subprocess
import time
from pathlib import Path

import requests


def ci_service(rep, srv):
    last_commit = (
        subprocess.check_output(["git", "-C", rep, "rev-parse", "HEAD"])
        .strip()
        .decode("utf-8")
    )
    new_commits = []

    while True:
        current_commit = (
            subprocess.check_output(["git", "-C", rep, "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
        if current_commit != last_commit:
            new_commits.append(current_commit)
            last_commit = current_commit

        time.sleep(1)

        if new_commits and time.time() % 10 < 1:
            for commit in new_commits:
                r1 = requests.post(
                    srv,
                    json={"commit_hash": commit, "step_name": "lint", "repo_path": rep},
                )
                r2 = requests.post(
                    srv,
                    json={
                        "commit_hash": commit,
                        "step_name": "build",
                        "repo_path": rep,
                    },
                )
                r3 = requests.post(
                    srv,
                    json={"commit_hash": commit, "step_name": "test", "repo_path": rep},
                )
                new_commits.remove(commit)
                print(r1, r2, r3)


def main() -> None:
    # get absolute path
    repo_path = str(Path.cwd().resolve())
    server_url = "http://localhost:8080"

    ci_service(repo_path, server_url)


if __name__ == "__main__":
    main()
